#!/usr/bin/env python

# from osmnx._downloader import _osm_network_download
from functools import partial

import osmnx as ox
import pandas as pd
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


def main():
    log("start")
    polygon = read_dataframe("data/britain-simple.geojson")
    polygon = polygon.explode(index_parts=False).reset_index(drop=True)
    polygon = polygon.loc[polygon.area.sort_values(ascending=False).index]
    polygon = polygon.to_crs(WGS84).iloc[0, 0]
    log("download railway")
    ox.settings.useful_tags_node = (
        "ref,changeset,id,version,uid,ref:tiploc,name,electrified,frequency,voltage,railway,layer,"
        "level"
    ).split(",")
    ox.settings.useful_tags_way = (
        "bridge,tunnel,width,id,maxspeed,junction,name,version,uid,changeset,landuse,timestamp,"
        "user,ref,oneway,ref:tiploc,name,electrified,frequency,voltage,railway,layer,level"
    ).split(",")
    # tags = (
    #    "rail|subway|light_rail|tram|narrow_gauge|disused|abandoned|construction|razed|"
    #    "dismantled"
    # ).split("|")
    # railway = ox.features.features_from_polygon(polygon, {"railway": tags})
    exclude = (
        "highway|cycleway|footway|path|pedestrian|steps|corridor|elevator|escalator|bridleway|"
        "platform|raceway|service|subway_entrance|disused_station"
    )
    include = (
        "rail|subway|light_rail|tram|narrow_gauge|disused|abandoned|construction|razed|"
        "dismantled"
    )
    custom_filter = f'["railway"~"{include}"]["railway"!~"{exclude}"]'
    log("Create network")
    railway = ox.graph.graph_from_polygon(
        polygon, simplify=False, retain_all=True, custom_filter=custom_filter
    )
    log("Create GeoPandas dataframe")
    node, edge = ox.graph_to_gdfs(railway)
    r = node.reset_index().fillna("").to_crs(CRS)
    r["geometry"] = r["geometry"].map(set_precision_one)
    #ix = r.within(polygon) | r.intersects(polygon)
    #r["location"] = "GB"
    #r.loc[~ix, "location"] = "-"
    log("Output GeoPKG full nodes")
    write_dataframe(r.to_crs(CRS), OUTPATH, layer="full_node")
    r = edge.reset_index().fillna("").to_crs(CRS)
    r["geometry"] = r["geometry"].map(set_precision_one)
    #ix = r.within(polygon) | r.intersects(polygon)
    #r["location"] = "GB"
    #r.loc[~ix, "location"] = "-"
    log("Output GeoPKG full lines")
    write_dataframe(r.to_crs(CRS), OUTPATH, layer="full_line")
    log("Simplify network")
    railway = ox.simplify_graph(railway)
    log("Create GeoPandas dataframe")
    node, edge = ox.graph_to_gdfs(railway)
    r = node.reset_index().fillna("").to_crs(CRS)
    r["geometry"] = r["geometry"].map(set_precision_one)
    #ix = r.within(polygon) | r.intersects(polygon)
    #r["location"] = "GB"
    #r.loc[~ix, "location"] = "-"
    log("Output GeoPKG nodes")
    node["geometry"] = node["geometry"].map(set_precision_one)
    write_dataframe(r.to_crs(CRS), OUTPATH, layer="node")
    r = edge.reset_index().fillna("").to_crs(CRS)
    r["geometry"] = r["geometry"].map(set_precision_one)
    #ix = r.within(polygon) | r.intersects(polygon)
    #r["location"] = "GB"
    #r.loc[~ix, "location"] = "-"
    log("Output GeoPKG lines")
    write_dataframe(r.to_crs(CRS), OUTPATH, layer="line")
    output = r.to_json(na="drop", drop_id=True)
    with open("great-britain-rail.geojson", "w", encoding="utf8") as fout:
        fout.write(output)


if __name__ == "__main__":
    main()
