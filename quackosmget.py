#!/usr/bin/env python3

import os
from functools import partial

import geopandas as gp
import pandas as pd
import polars as pl
import quackosm as qosm
from shapely.ops import transform

WGS84 = "EPSG:4326"
# CRS = "EPSG:4087"
CRS = "EPSG:27700"

OUTPATH = "output/ine-track.gpkg"

pd.set_option("display.max_columns", None)


def _set_precision(precision=6):
    """set_precision:"""

    def _precision(x, y, z=None):
        return tuple([round(i, precision) for i in [x, y, z] if i])

    return partial(transform, _precision)


def list_files(filepath, key=".pbf"):
    """list_files:"""
    files = ()
    for d, _, filenames in os.walk(filepath):
        files = files + tuple("{}/{}".format(d, f) for f in filenames if key in f)
    return files


def set_parquet():
    """set_parquet:"""
    for pbf_path in list_files("data"):
        filestub = os.path.basename(pbf_path).split(".")[0]
        print(filestub)
        if list_files("output", filestub) != ():
            continue
        _ = qosm.convert_pbf_to_parquet(
            pbf_path,
            tags_filter={"railway": True},
            keep_all_tags=True,
            result_file_path=f"output/{filestub}.parquet",            
        )


def get_rail(chunk=500_000):
    """get_rail:"""
    data = []
    for filepath in list_files("output", ".parquet"):
        print(filepath)
        if "britain" not in filepath:
            continue
        r = pl.read_parquet(filepath)
        column = (
            """railway,ref,name,ref:tiploc,ref:stanox,maxspeed,electrified,frequency,"""
            """voltage,junction,bridge,width,tunnel,oneway,landuse,geometry"""
        ).split(",")
        r = (
            r.explode("tags", empty_as_null=True)
            .unnest("tags")
            .filter(pl.col("key").is_in(column))
            .pivot(index=["feature_id", "geometry"], on="key", values="value")
        )
        data.append(r)
    return pl.concat(data)


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
    set_parquet()
    rail = get_rail()
    write_geopanda(rail, "base")

    inactive_filter = (
        """highway,cycleway,footway,path,pedestrian,steps,corridor,elevator,escalator,"""
        """proposed,construction,bridleway,abandoned,platform,raceway,service"""
    ).split(",")
    railway_filter = "rail,subway,light_rail,tram,narrow_gauge".split(",")
    # railway {0: inactive, 1: other, 2: rail/metro
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
            (pl.col("electrified") == "contact_line") & ~pl.col("voltage").is_in(["", "0"])
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
    print(OUTPATH)

if __name__ == "__main__":
    main()
    
