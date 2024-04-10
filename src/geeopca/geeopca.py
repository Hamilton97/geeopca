from __future__ import annotations
from dataclasses import dataclass, InitVar
from typing import Callable

import json

import ee

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

from timezonefinder import TimezoneFinder


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# EarthEngineConversion
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def convert2feature(image: ee.Image) -> ee.Feature:
    x = ee.Image(image)
    return ee.Feature(
        x.geometry(),
        {
            "sysid": x.get("system:index"),
            "utc": x.get("system:time_start"),
            "system_prefix": x.get("prefix"),
        },
    )


def convert_to_feature_collection(dataset: EarthEngineDataset) -> ee.FeatureCollection:
    ee_list = dataset.dataset.toList(dataset.size())
    features = ee_list.map(convert2feature)
    return ee.FeatureCollection(features)


def convert_2_dataframe(dataset: EarthEngineDataset) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame.from_features(
        convert_to_feature_collection(dataset).getInfo()["features"]
    )


def gdf_to_ee_feature_collection(gdf: gpd.GeoDataFrame):
    return ee.FeatureCollection(gdf.__geo_interface__)


def load_geometry_from_file(filename: str) -> ee.Geometry:
    gdf = gdf.read_file(filename)
    eedata = gdf_to_ee_feature_collection(gdf)
    return eedata.first().geometry()


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# Geo and Data frame processing functions
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def process_system_index(row):
    elements = row.split("_")
    return "_".join([elm for elm in elements if not elm.isdigit()])


def make_system_index(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf["sysid"] = gdf["sysid"].apply(process_system_index)
    gdf["system_index"] = gdf["system_prefix"] + "/" + gdf["sysid"]
    return gdf


def process_date_time(df: gpd.GeoDataFrame | pd.DataFrame):
    tf = TimezoneFinder()
    df["x"] = df.geometry.centroid.x
    df["y"] = df.geometry.centroid.y
    df["timezone"] = df.apply(lambda x: tf.timezone_at(lng=x["x"], lat=x["y"]), axis=1)
    df["utc"] = df["utc"] / 1000.0
    df["timestamp"] = pd.to_datetime(df["utc"], unit="s")
    df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
    df["timestamp"] = df.apply(
        lambda row: row["timestamp"].tz_convert(row["timezone"]), axis=1
    )
    df["year"] = df["timestamp"].dt.year
    df["julian_date"] = df["timestamp"].dt.dayofyear
    return df


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# Plotting
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #


def date_time_scatter_plot(df: gpd.GeoDataFrame | pd.DataFrame) -> plt.Figure:
    # Create a scatter plot
    fig, ax = plt.subplots()
    # Create a scatter plot on the axes

    ax.scatter(df["julian_date"], df["year"], alpha=0.5)

    # Set the limits for the x-axis and y-axis
    ax.set_xlim([1, 366])  # Julian dates range from 1 to 366
    ax.set_ylim(
        [df["year"].min() - 1, df["year"].max() + 1]
    )  # Years range from min to max year in the data

    # Set major tick marks every 50 on the x-axis and every 1 on the y-axis
    ax.set_xticks(range(0, 366, 50))
    ax.set_yticks(range(df["year"].min() - 1, df["year"].max() + 1, 1))

    ax.set_xlabel("Julian Day")
    ax.set_ylabel("Year")
    ax.set_title("Occurrence of Julian Days by Year")

    ax.grid(True)
    return fig


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# I/O
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def gdf_to_json(gdf: gpd.GeoDataFrame, filename: str = None) -> None:
    filename = filename or "data.json"
    if not filename.endswith(".json"):
        filename = f"{filename}.json"

    grouped_df = gdf.groupby("year")
    json_data = {}
    for year, df in grouped_df:
        data = {year: df["system_index"].tolist()}
        json_data.update(data)

    with open("data.json", "w") as fh:
        json.dump(json_data, fh, indent=4)


def save_plot(figure: plt.Figure, filename: str = None) -> None:
    filename = filename or "plot.png"
    figure.savefig(filename)


def load_json_data(jsonfile) -> dict[str, list[str]]:
    with open(jsonfile, "r") as fh:
        return json.load(h)
