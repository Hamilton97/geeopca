import os
import sys

from dataclasses import dataclass
from typing import Any

import ee
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

from timezonefinder import TimezoneFinder


DATASET = "s2"  # 1,2,3,4
SPATIAL_FILE = "users/ryangilberthamilton/bq-trend-analysis/subset_BoQ_for_Ken_v2"
OUTPUT_DIR = "."
PLOT_NAME = "figure.png"
TABLE_NAME = "table.csv"
START_DATE_YYYY_MM_dd = "2017-04-01"
END_DATE_YYYY_MM_dd = "2022-10-31"


@dataclass
class Dataset:
    id: str
    cloud: str


datasets = {
    "s2": Dataset(id="COPERNICUS/S2_HARMONIZED", cloud="CLOUDY_PIXEL_PERCENTAGE")
}


def spatialfile2ee(filename: str) -> ee.Geometry:
    if filename.endswith(".shp"):
        gdf = gpd.read_file(filename)
        first_row = gdf.iloc[[0]].to_crs(4326)
        return ee.FeatureCollection(first_row.__geo_interface__).geometry()
    return ee.FeatureCollection(filename).first().geometry()


def date_chunks(start: str, end: str) -> list[tuple[str, str]]:
    start, end = start.split("-"), end.split("-")
    syear, endyear = int(start.pop(0)), int(end.pop(0))
    return [
        (f"{year}-{start[0]}-{start[1]}", f"{year}-{end[0]}-{end[1]}")
        for year in range(syear, endyear + 1)
    ]


def fetch_and_convert_ee_data(
    arg: str, aoi: Any, start: str, stop: str, cloud_property: str
):
    def convert2feature(image):
        x = ee.Image(image)
        return ee.Feature(
            x.geometry(),
            {
                "syspath": x.get("syspath"),
                "utc": x.get("system:time_start"),
            },
        )

    rsd = (
        ee.ImageCollection(arg)
        .filterBounds(aoi)
        .filterDate(start, stop)
        .filter(ee.Filter.lte(cloud_property, 0.0))
        .map(lambda x: x.set("syspath", ee.String(arg).cat("/").cat(x.id())))
    )

    ee_list = rsd.toList(rsd.size())
    features = ee_list.map(convert2feature)
    # data transform to featurecollection
    fc = ee.FeatureCollection(features)
    # convert to GeoDataFrame
    gdf = gpd.GeoDataFrame.from_features(fc.getInfo()["features"])
    return gdf


def localize_utc_time(df: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    # date time conversion
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


def main():

    aoi = spatialfile2ee(SPATIAL_FILE)
    data = datasets.get(DATASET)
    date_ranges = date_chunks(START_DATE_YYYY_MM_dd, END_DATE_YYYY_MM_dd)

    gdfs = [
        fetch_and_convert_ee_data(data.id, aoi, start, stop, data.cloud)
        for start, stop in date_ranges
    ]

    gdf = pd.concat(gdfs)

    gdf = localize_utc_time(gdf)

    fig = date_time_scatter_plot(gdf)
    fig.savefig("figure.png")

    gdf = gdf[[col for col in gdf.columns if col != "geometry"]]
    gdf.to_csv("table.csv")

    return 0


if __name__ == "__main__":
    ee.Initialize()
    sys.exit(main())
