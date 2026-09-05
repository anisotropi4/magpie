#!/usr/bin/env python3
"""quackosmget: extract rail related INE data from OSM"""

import os

import geopandas as gp
import pandas as pd
import polars as pl
import quackosm as qosm

WGS84 = "EPSG:4326"
# CRS = "EPSG:4087"
CRS = "EPSG:27700"

OUTPATH = "output/ine-rail.gpkg"

pd.set_option("display.max_columns", None)


def _pp(df, n=100, m=15):
    """pp: pretty print polar frame"""
    with pl.Config(set_tbl_cols=-1, set_tbl_rows=n, set_tbl_hide_dataframe_shape=True):
        try:
            r = df.collect()
        except AttributeError:
            r = df
        column = r.columns
        for i in range(0, len(column), m):
            chunk = r.columns[i : i + m]
            print(r[chunk])
    print(r.shape)


def list_files(filepath, key=".pbf"):
    """list_files:"""
    files = ()
    for d, _, filenames in os.walk(filepath):
        files = files + tuple(f"{d}/{f}" for f in filenames if key in f)
    return iter(files)


def set_parquet():
    """set_parquet:"""
    pbf_path = next(list_files("data", "britain"))
    filestub = os.path.basename(pbf_path).split(".")[0]
    try:
        next(list_files("output", filestub))
        return
    except StopIteration:
        pass
    print(filestub)
    _ = qosm.convert_pbf_to_parquet(
        pbf_path,
        # tags_filter={"type": ["route", "route_master"], "network": True, "railway": True, "rail": True, "train": True, "network:metro": True},
        tags_filter={"railway": True, "rail": True, "train": True},
        keep_all_tags=True,
        result_file_path=f"output/{filestub}.parquet",
    )


def get_parquet(key):
    """set_parquet:"""
    pbf_path = next(list_files("data", "britain"))
    filestub = os.path.basename(pbf_path).split(".")[0]
    print(filestub, key)
    return qosm.convert_pbf_to_geodataframe(
        pbf_path,
        keep_all_tags=True,
        filter_osm_ids=[key],
    )


def get_rail():
    """get_rail:"""
    data = []
    for filepath in list_files("output", ".parquet"):
        if "britain" not in filepath:
            continue
        print(filepath)
        r = pl.read_parquet(filepath)
        column = (
            """railway,ref,name,ref:tiploc,ref:stanox,maxspeed,electrified,frequency,voltage,"""
            """line,operator,junction,bridge,width,tunnel,oneway,landuse,geometry,network,route"""
        ).split(",")
        r = (
            r.explode("tags", empty_as_null=True)
            .unnest("tags")
            .filter(pl.col("key").is_in(column))
            .pivot(index=["feature_id", "geometry"], on="key", values="value")
        )
        data.append(r)
    return pl.concat(data)


def get_overground(rail):
    """get_london_overground:"""
    r = []
    for k in ["Liberty", "Lioness", "Mildmay", "Suffragette", "Weaver", "Windrush"]:
        df = rail.filter(pl.col("line").str.contains(k)).with_columns(
            network_name=pl.lit(k)
        )
        r.append(df)
    return pl.concat(r)


def get_geopanda(df):
    """get_geopandas:"""
    r = gp.GeoDataFrame(
        df.to_pandas(),
        geometry=gp.GeoSeries.from_wkb(df.select("geometry").to_series()),
        crs=WGS84,
    )
    return r.to_crs(CRS)


def write_geopanda(df, layer, outfile=OUTPATH):
    """write_geopandas:"""
    get_geopanda(df).to_file(outfile, layer=layer)


def main():
    """main: script execution function"""
    set_parquet()
    rail = get_rail()
    write_geopanda(rail, "base")
    inactive_filter = (
        """highway,cycleway,footway,path,pedestrian,steps,corridor,elevator,escalator,"""
        """proposed,construction,bridleway,abandoned,platform,raceway,service"""
    ).split(",")
    railway_filter = "rail,subway,light_rail,tram,narrow_gauge,network".split(",")
    # railway {0: inactive, 1: other, 2: rail/metro}
    rail = rail.with_columns(
        rail=pl.when(pl.col("railway").str.contains_any(inactive_filter))
        .then(pl.lit(0))
        .when(pl.col("railway").str.contains_any(railway_filter))
        .then(pl.lit(2))
        .otherwise(1),
        mx=pl.when(pl.col("railway").str.contains_any(railway_filter))
        .then(
            pl.col("maxspeed")
            .str.to_lowercase()
            .str.replace_all(r"\s*mph\s*", "")
            .cast(pl.Float32)
        )
        .fill_null(-1.0),
        id=pl.when(
            (pl.col("electrified") == "contact_line")
            & ~pl.col("voltage").is_in(["", "0"])
        )
        .then(pl.lit("OCL"))
        .when(pl.col("electrified") == "rail")
        .then(pl.lit("3rd rail"))
        .when(pl.col("electrified") == "4th_rail")
        .then(pl.lit("4th rail"))
        .when(pl.col("electrified") == "contact_line;rail")
        .then(pl.lit("Dual OCL 3rd rail"))
        .otherwise(pl.lit("None")),
    )
    write_geopanda(rail.filter(pl.col("rail") == 2).fill_null(""), "rail")
    overground = get_overground(rail)
    write_geopanda(overground.fill_null(""), layer="Overground")
    print(OUTPATH)


if __name__ == "__main__":
    main()
