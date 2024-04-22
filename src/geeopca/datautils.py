from typing import Any
import json

import ee
import geopandas as gpd
import pandas as pd


def spatialfile2ee(filename: str) -> ee.Geometry:
    gdf = gpd.read_file(filename)
    first_row = gdf.iloc[[0]]
    return ee.FeatureCollection(first_row.__geo_interface__).geometry()


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