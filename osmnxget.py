#!/usr/bin/env python

# from osmnx._downloader import _osm_network_download
from functools import partial

import osmnx as ox
import pandas as pd
import geopandas as gp
import numpy as np
from osmnx.utils import log
from pyogrio import read_dataframe, write_dataframe
from shapely import set_precision

ox.settings.use_cache = True
ox.settings.log_console = True

# ox.settings.overpass_rate_limit = False

OUTPATH = "great-britain-rail.gpkg"
CRS = "EPSG:32630"
# British National Grid
CRS = "EPSG:27700"
WGS84 = "EPSG:4326"

pd.set_option("display.max_columns", None)

set_precision_one = partial(set_precision, grid_size=1.0)

def get_node_group(this_graph, key):
    _, edge = ox.graph_to_gdfs(this_graph)
    r = edge[["railway"]].groupby(key)
    group = dict(list(r))
    r = {}
    for k, v in group.items():
        node_id = v.reset_index().values[:, 0:2].reshape(-1)
        r[k] = np.unique(node_id)
    return r

def get_simplified_nx(this_graph, node_id, key):
    r = this_graph.subgraph(node_id)
    r = ox.simplify_graph(r)
    node, edge = ox.graph_to_gdfs(r)
    edge["railway"] = key
    return node, edge

def get_network(polygon):
    log("download railway")
    ox.settings.useful_tags_node = (
        "ref,changeset,id,version,uid,ref:tiploc,name,electrified,frequency,voltage,railway,layer,"
        "level"
    ).split(",")
    ox.settings.useful_tags_way = (
        "bridge,tunnel,width,id,maxspeed,junction,name,version,uid,changeset,landuse,timestamp,"
        "user,ref,oneway,ref:tiploc,name,electrified,frequency,voltage,railway,layer,level"
    ).split(",")
    include = (
        "rail|proposed|construction|disused|abandoned|razed|narrow_gauge|light_rail|subway|"
        "tram"
    )
    exclude = (
        "highway|cycleway|footway|path|pedestrian|steps|corridor|elevator|escalator|bridleway|"
        "platform|raceway|service|subway_entrance|disused_station|tram_stop"
    )
    custom_filter = f'["railway"~"{include}"]["railway"!~"{exclude}"]'
    log("Create network")
    railway = ox.graph.graph_from_polygon(
        polygon, simplify=False, retain_all=True, custom_filter=custom_filter
    )
    log("Create GeoPandas dataframe")
    rail_nodes = get_node_group(railway, "railway")
    node, edge = gp.GeoDataFrame(), gp.GeoDataFrame()
    for k, v in rail_nodes.items():
        log(k)
        i, j = get_simplified_nx(railway, v, k)
        i, j = i.reset_index().fillna(""), j.reset_index().fillna("")
        node = pd.concat([i, node])
        edge = pd.concat([j, edge])
    return node, edge

def main():
    log("start")
    polygon = read_dataframe("data/britain-simple.geojson")
    polygon = polygon.explode(index_parts=False).reset_index(drop=True)
    polygon = polygon.loc[polygon.area.sort_values(ascending=False).index]
    polygon = polygon.to_crs(WGS84).iloc[0, 0]
    node, edge = get_network(polygon)
    r = node.reset_index().fillna("").to_crs(CRS)
    r["geometry"] = r["geometry"].map(set_precision_one)
    r = node.reset_index().fillna("").to_crs(CRS)
    r["geometry"] = r["geometry"].map(set_precision_one)
    log("Output GeoPKG nodes")
    node["geometry"] = node["geometry"].map(set_precision_one)
    write_dataframe(r.to_crs(CRS), OUTPATH, layer="node")
    r = edge.reset_index().fillna("").to_crs(CRS)
    r["geometry"] = r["geometry"].map(set_precision_one)
    log("Output GeoPKG lines")
    write_dataframe(r.to_crs(CRS), OUTPATH, layer="line")
    output = r.to_json(na="drop", drop_id=True)
    with open("great-britain-rail.geojson", "w", encoding="utf8") as fout:
        fout.write(output)
    log("finish")


if __name__ == "__main__":
    main()
