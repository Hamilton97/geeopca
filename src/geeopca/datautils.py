import json
import ee
import geopandas as gpd
import pandas as pd

from timezonefinder import TimezoneFinder


def image_collection_to_dataframe(image_collection: ee.ImageCollection) -> gpd.GeoDataFrame:
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

    ee_list = image_collection.toList(image_collection.size())
    features = ee_list.map(convert2feature)
    feature_col = ee.FeatureCollection(features)
    gdf = gpd.GeoDataFrame.from_features(feature_col.getInfo()["features"])
    return process_system_index(gdf)


def process_system_index(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    def remove_prefix(row):
        elements = row.split("_")
        return "_".join([elm for elm in elements if not elm.isdigit()])

    gdf["sysid"] = gdf["sysid"].apply(remove_prefix)
    gdf["system_index"] = gdf["system_prefix"] + "/" + gdf["sysid"]
    return gdf


def localize_utc_time(df: gpd.GeoDataFrame | pd.DataFrame):
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

    start, end = start.split('-'), end.split("-")
    syear, endyear = int(start.pop(0)), int(end.pop(0))
    return [(f'{year}-{start[0]}-{start[1]}', f'{year}-{end[0]}-{end[1]}') for year in range(syear, endyear + 1)]
