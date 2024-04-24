from typing import Any, Callable
import ee
import geopandas as gpd
import pandas as pd


def to_feature_collection(image_collection) -> ee.FeatureCollection:
    def convert2feature(image):
        x = ee.Image(image)
        return ee.Feature(
            x.geometry(),
            {
                "syspath": x.get("syspath"),
                "utc": x.get("system:time_start"),
            },
        )
    ee_list = image_collection.toList(image_collection.size())
    features = ee_list.map(convert2feature)
    return ee.FeatureCollection(features)


def get_data(
    arg: str, aoi: Any, start: str, stop: str, cloud_property: str
) -> gpd.GeoDataFrame:
    rsd =  (
        ee.ImageCollection(arg)
        .filterBounds(aoi)
        .filterDate(start, stop)
        .filter(ee.Filter.lte(cloud_property, 0.0))
        .map(lambda x: x.set("syspath", ee.String(arg).cat("/").cat(x.id())))
    )
    
    # data transform to featurecollection
    to_fc = to_feature_collection(rsd)
    
    # convert to GeoDataFrame
    gdf = gpd.GeoDataFrame.from_features(to_fc.getInfo()["features"])
    return gdf
