#!/usr/bin/env python3
"""quackplanetosmget: combine split OSM planet file to extract rail related tags"""

import os

import geopandas as gp
import pandas as pd
import polars as pl
import quackosm as qosm

WGS84 = "EPSG:4326"
# CRS = "EPSG:4087"
CRS = "EPSG:3857"

OUTPATH = "output/planet-rail.gpkg"

pd.set_option("display.max_columns", None)


def list_files(filepath, key=".pbf"):
    """list_files:"""
    files = ()
    for d, _, filenames in os.walk(filepath):
        files = files + tuple(f"{d}/{f}" for f in filenames if key in f)
    return files


def set_parquet():
    """set_parquet:"""
    for pbf_path in list_files("planet"):
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


def get_rail():
    """get_rail:"""
    data = []
    for filepath in sorted(list_files("output", ".parquet")):
        if "planet" not in filepath:
            continue
        print(filepath)
        r = pl.read_parquet(filepath)
        column = (
            """railway,ref,name,maxspeed,electrified,frequency,voltage,"""
            """junction,bridge,width,tunnel,oneway,landuse,geometry"""
        ).split(",")
        r = (
            r.explode("tags", empty_as_null=True)
            .unnest("tags")
            .filter(pl.col("key").is_in(column))
            .pivot(index=["feature_id", "geometry"], on="key", values="value")
            .with_columns(
                america=pl.lit((len(data) >= 2) and (len(data) < 12)),
            )
        )
        data.append(r)
    return pl.concat(data, how="diagonal_relaxed").fill_null("")


def get_active_rail(rail):
    """get_active_rail:"""
    inactive_filter = (
        """highway,cycleway,footway,path,pedestrian,steps,corridor,elevator,escalator,"""
        """proposed,construction,bridleway,abandoned,platform,raceway,service"""
    ).split(",")
    railway_filter = "rail,subway,light_rail,tram,narrow_gauge".split(",")
    # railway {0: inactive, 1: other, 2: rail/metro
    r = (
        rail.with_columns(
            rail=pl.when(pl.col("railway").str.contains_any(inactive_filter))
            .then(pl.lit(0))
            .when(pl.col("railway").str.contains_any(railway_filter))
            .then(pl.lit(2))
            .otherwise(1),
            mx=pl.when(pl.col("railway").str.contains_any(railway_filter)).then(
                pl.col("maxspeed")
                .str.to_lowercase()
                .str.replace_all(r"\s*mph\s*", "")
                .str.replace_all(r"\s*km/h\s*", "")
                .str.replace_all(r"[c>\\+]", "")
                .str.replace_all("4o", "40")
                .str.replace_all("\\.\\.", ";")
                .str.replace_all("\\(90\\)", "")
                .str.replace_all(r"^\D+$", "")
                .str.split(";")
                .list.max()
                .str.strip_chars()
            ),
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
        .with_columns(
            mx=pl.when(pl.col("mx") == "")
            .then(pl.lit("0"))
            .otherwise(pl.col("mx"))
            .fill_null("-1.0")
            .cast(pl.Float32)
        )
        .with_columns(
            kmh=pl.when(pl.col("maxspeed").str.contains("mph"))
            .then(pl.col("mx") * 1.609344)
            .when(pl.col("mx") < 0.0)
            .then(pl.lit(0.0))
            .otherwise(pl.col("mx"))
        )
        .drop("mx")
        .sort("kmh")
        .unique("feature_id")
    )
    return r


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
    r = get_geopanda(df).explode()
    r.to_file(outfile, layer=layer)


def main():
    """main: core execution functions"""
    set_parquet()
    rail = get_rail()
    write_geopanda(rail.drop("america"), "base", "output/planet-base.gpkg")
    rail = get_active_rail(rail)
    write_geopanda(rail.filter(pl.col("rail") == 2).fill_null(""), "rail")
    america = rail.filter(pl.col("america")).drop("america")
    africaustraeurasia = rail.filter(~pl.col("america")).drop("america")
    write_geopanda(
        america.filter(pl.col("rail") == 2).fill_null(""),
        "rail",
        "output/america-rail.gpkg",
    )
    write_geopanda(
        africaustraeurasia.filter(pl.col("rail") == 2).fill_null(""),
        "rail",
        "output/africaustraeurasia-rail.gpkg",
    )
    print(OUTPATH)


if __name__ == "__main__":
    main()
