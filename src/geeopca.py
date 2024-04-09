from __future__ import annotations
from dataclasses import dataclass, InitVar
from typing import Callable


import ee

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

from timezonefinder import TimezoneFinder


#
# Earth Engine Datasets
#


@dataclass
class EarthEngineDataset:
    id: str
    aoi: InitVar[ee.Geometry | ee.FeatureCollection]
    dates: InitVar[list[tuple[str, str]]]

    def __post_init__(self, aoi, dates):

        self.dataset = None
        for date in dates:
            if self.dataset is None:
                self.dataset = self.make_dataset(self.id, date, aoi)
                continue
            self.dataset = self.dataset.merge(self.make_dataset(self.id, date, aoi))

    @property
    def utc_dates(self) -> ee.List:
        return (
            self.dataset.aggregate_array("system:time_start")
            .map(lambda x: ee.Date(x).format("YYYY-MM-dd"))
            .distinct()
        )

    def add_system_prefix(self):
        func = lambda x: x.set(
            "sys_idx", ee.String(self.id).cat("/").cat(x.get("system:index"))
        )
        self.dataset = self.dataset.map(func)
        return self

    def filter_out_clouds(self, property: str, value: int | float = 0.0):
        self.dataset = self.dataset.filter(ee.Filter.lte(property, value))
        return self

    def map(self, algo: Callable):
        self.dataset = self.dataset.map(algo)
        return self

    def size(self) -> ee.Number:
        return self.dataset.size()

    def build(self) -> ee.ImageCollection:
        return self.dataset

    @staticmethod
    def make_dataset(id, date, aoi):
        return ee.ImageCollection(id).filterBounds(aoi).filterDate(*date)


# EarthEngineConversion
def convert2feature(image: ee.Image) -> ee.Feature:
    x = ee.Image(image)
    return ee.Feature(
        x.geometry(),
        {"sysid": x.get("system:index"), "utc": x.get("system:time_start")},
    )


def convert_to_feature_collection(dataset: EarthEngineDataset) -> ee.FeatureCollection:
    ee_list = dataset.dataset.toList(dataset.size())
    features = ee_list.map(convert2feature)
    return ee.FeatureCollection(features)


def convert_2_dataframe(dataset: EarthEngineDataset) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame.from_features(
        convert_to_feature_collection(dataset).getInfo()["features"]
    )


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# Geo and Data frame processing functions
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #


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


#
# Plotting
#


def date_time_scatter_plot(df: gpd.GeoDataFrame | pd.DataFrame, filename: str) -> None:
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
