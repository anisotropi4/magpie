#!/usr/bin/env python

import json
import osmnx as ox
from osmnx.utils import log
from osmnx.downloader import _osm_network_download
from functools import partial
from itertools import groupby

from shapely.geometry import shape, Point, LineString
from shapely.ops import transform
from pyogrio import read_dataframe, write_dataframe
import geopandas as gp

ox.settings.use_cache = True
ox.settings.log_console = True

ox.settings.overpass_rate_limit = False

FILEPATH = "gb-rail.gpkg"
CRS = "EPSG:32630"
WGS84 = "EPSG:4326"

try:
    import pandas as pd

    pd.set_option("display.max_columns", None)
except ImportError:
    pass


def _set_precision(precision=6):
    def _precision(x, y, z=None):
        return tuple([round(i, precision) for i in [x, y, z] if i])

    return partial(transform, _precision)


def get_node(e):
    node = {"geometry": Point(e["lon"], e["lat"])}
    node["osmid"] = e["id"]
    if "tags" in e:
        for t in ox.settings.useful_tags_node:
            if t in e["tags"]:
                node["tags"] = True
                node[t] = e["tags"][t]
    return node


def get_path(e):
    path = {}
    path["osmid"] = e["id"]
    # remove any consecutive duplicate elements in the list of nodes
    g_list = groupby(e["nodes"])
    path["nodes"] = [g[0] for g in g_list]
    if "tags" in e:
        for t in ox.settings.useful_tags_path:
            if t in e["tags"]:
                path[t] = e["tags"][t]
    return path


def get_linestring(v):
    return LineString([NODES[i]["geometry"] for i in v])


# with open('great-britain.json', 'r') as fin:
#    POLYGON = shape(json.load(fin))

POLYGON = read_dataframe("data/britain-simple.geojson").explode(index_parts=True)
POLYGON = POLYGON.loc[POLYGON.area.sort_values(ascending=False).index]
POLYGON = POLYGON.to_crs("EPSG:4326").iloc[0, 0]

log("download railway")
ox.settings.useful_tags_node = [
    "lon",
    "timestamp",
    "user",
    "lat",
    "ref",
    "changeset",
    "id",
    "version",
    "uid",
    "ref:tiploc",
    "name",
    "electrified",
    "frequency",
    "voltage",
    "railway",
    "layer",
    "level",
]
ox.settings.useful_tags_path = [
    "bridge",
    "tunnel",
    "width",
    "id",
    "maxspeed",
    "junction",
    "name",
    "version",
    "uid",
    "changeset",
    "landuse",
    "timestamp",
    "user",
    "ref",
    "oneway",
    "ref:tiploc",
    "name",
    "electrified",
    "frequency",
    "voltage",
    "railway",
    "layer",
    "level",
]

RAILWAY = _osm_network_download(
    POLYGON,
    'way["railway"]',
    '["railway"!~"highway|cycleway|footway|path|pedestrian|steps|corridor|elevator|escalator|bridleway|platform|raceway|service|subway_entrance|disused_station"]["railway"~"rail|subway|light_rail|tram|narrow_gauge|disused|abandoned|construction|razed|dismantled"]',
)

log("Create node and path data")
NODES = {}
PATHS = {}
for osm_data in RAILWAY:
    for e in osm_data["elements"]:
        if e["type"] == "node":
            key = e["id"]
            NODES[key] = get_node(e)
        if e["type"] == "way":  # osm calls network paths 'ways'
            key = e["id"]
            PATHS[key] = {**get_path(e), **{"class": "rail"}}

log("Create LineString GeoPandas dataframe")
GF1 = gp.GeoDataFrame.from_dict(PATHS, orient="index")
GF1["geometry"] = GF1["nodes"].apply(get_linestring)
GF1 = GF1.drop("nodes", axis=1)
GF1 = GF1.set_crs(WGS84).fillna("")
GF1["type"] = "way"
IDX1 = GF1.within(POLYGON) | GF1.intersects(POLYGON)
GF1["location"] = "GB"
GF1.loc[~IDX1, "location"] = "-"
log("Output GeoPKG lines")
write_dataframe(GF1.to_crs(CRS), FILEPATH, layer="lines")

log("Create Point GeoPandas dataframe")
GF2 = gp.GeoDataFrame.from_dict(data=NODES, orient="index").set_crs(WGS84)
GF2 = GF2.loc[GF2["tags"].dropna().index].drop(columns="tags", axis=1)
GF2 = GF2.fillna("")
GF2["type"] = "node"
IDX2 = GF2.within(POLYGON) | GF2.intersects(POLYGON)
GF2["location"] = "GB"
GF2.loc[~IDX2, "location"] = "-"
log("Output GeoPKG")
write_dataframe(GF2.to_crs(CRS), FILEPATH, layer="nodes")

log("Write output file")
OUTPUT = GF1.to_json(na="drop", drop_id=True)
with open("gb-rail.geojson", "w") as fout:
    fout.write(OUTPUT)
