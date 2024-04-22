from typing import Any, Callable
import ee
import geopandas as gpd
import pandas as pd

from timezonefinder import TimezoneFinder


class RemoteSenesingDataset:
    def __init__(
        self, id: str, aoi: str, start: str, end: str, cloud_property: str
    ) -> None:
        self.prefix = id
        self.rsd = (
            ee.ImageCollection(self.prefix)
            .filterDate(start, end)
            .filterBounds(aoi)
            .filter(ee.Filter.lte(cloud_property, 0.0))
            .map(self.insert_system_prefix(id))
        )

    def __add__(self, other):
        if not isinstance(other, RemoteSenesingDataset):
            raise TypeError("Other must be of type RemoteSensing Dataset")
        self.rsd = self.rsd.merge(other.rsd)
        return self

    def map(self, algo: Callable):
        self.rsd = self.rsd.map(algo)
        return self

    def to_dataframe(self) -> gpd.GeoDataFrame:
        def convert2feature(image):
            x = ee.Image(image)
            return ee.Feature(
                x.geometry(),
                {
                    "syspath": x.get("syspath"),
                    "utc": x.get("system:time_start"),
                },
            )

        ee_list = self.rsd.toList(self.rsd.size())
        features = ee_list.map(convert2feature)
        feature_col = ee.FeatureCollection(features)
        df = gpd.GeoDataFrame.from_features(feature_col.getInfo()["features"])
        
        # date time conversion
        tf = TimezoneFinder()
        df["x"] = df.geometry.centroid.x
        df["y"] = df.geometry.centroid.y
        df["timezone"] = df.apply(
            lambda x: tf.timezone_at(lng=x["x"], lat=x["y"]), axis=1
        )
        df["utc"] = df["utc"] / 1000.0
        df["timestamp"] = pd.to_datetime(df["utc"], unit="s")
        df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
        df["timestamp"] = df.apply(
            lambda row: row["timestamp"].tz_convert(row["timezone"]), axis=1
        )
        df["year"] = df["timestamp"].dt.year
        df["julian_date"] = df["timestamp"].dt.dayofyear
        return df

    @staticmethod
    def insert_system_prefix(prefix: str) -> Callable:
        return lambda x: x.set("syspath", ee.String(prefix).cat("/").cat(x.id()))

    @staticmethod
    def compute_ndvi(nir, red):
        return lambda x: x.addBands(x.normalizedDifference([nir, red]).rename("NDVI"))


class Sentinel2TOA(RemoteSenesingDataset):
    def __init__(self, aoi: str, start: str, end: str) -> None:
        super().__init__(
            "COPERNICUS/S2_HARMONIZED", aoi, start, end, "CLOUDY_PIXEL_PERCENTAGE"
        )
