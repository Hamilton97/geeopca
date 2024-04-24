from typing import Any
import json

import ee
import geopandas as gpd
import pandas as pd

from timezonefinder import TimezoneFinder


def spatialfile2ee(filename: str) -> ee.Geometry:
    gdf = gpd.read_file(filename)
    first_row = gdf.iloc[[0]]
    return ee.FeatureCollection(first_row.__geo_interface__).geometry()


def localize_utc(df: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
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


def date_chunks(start: str, end: str):
    """
    Generate a list of date chunks between the given start and end dates.

    Args:
        start (str): The start date in the format 'YYYY-MM-DD'.
        end (str): The end date in the format 'YYYY-MM-DD'.

    Returns:
        list: A list of tuples representing the date chunks. Each tuple contains the start and end dates of a chunk.

    Example:
        >>> date_chunks('2022-01-01', '2022-12-31')
        [('2022-01-01', '2022-01-31'), ('2022-02-01', '2022-02-28'), ..., ('2022-12-01', '2022-12-31')]
    """

    start, end = start.split("-"), end.split("-")
    syear, endyear = int(start.pop(0)), int(end.pop(0))
    return [
        (f"{year}-{start[0]}-{start[1]}", f"{year}-{end[0]}-{end[1]}")
        for year in range(syear, endyear + 1)
    ]


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


class DateRanger:
    def __init__(self, start: str, end: str) -> None:
        self.steps = self.compute_date_ranges(start, end)

    def __len__(self) -> int:
        return len(self.steps)

    def __getitem__(self, __idx: int) -> Any:
        return self.steps[__idx]

    @staticmethod
    def compute_date_ranges(start, end) -> list[tuple[str, str]]:
        start, end = start.split("-"), end.split("-")
        syear, endyear = int(start.pop(0)), int(end.pop(0))
        return [
            (f"{year}-{start[0]}-{start[1]}", f"{year}-{end[0]}-{end[1]}")
            for year in range(syear, endyear + 1)
        ]
