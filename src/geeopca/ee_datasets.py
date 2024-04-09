import ee


def get_dataset(
    dataset_id: str, property: str, aoi: ee.Geometry, dates: list[tuple[str, str]]
) -> ee.ImageCollection:

    dataset = None
    for date in dates:
        if dataset is None:
            dataset = ee.ImageCollection(dataset_id).filterBounds(aoi).filterDate(*date)
        dataset = dataset.merge(
            ee.ImageCollection(dataset_id).filterBounds(aoi).filterDate(*date)
        )

    dataset = dataset.filter(ee.Filter.lte(property, 0.0)).map(
        lambda x: x.set("prefix", dataset_id)
    )
    return dataset


def get_s2_toa(aoi: ee.Geometry, dates: list[tuple[str, str]]) -> ee.ImageCollection:
    return get_dataset(
        "COPERNICUS/S2_HARMONIZED", "CLOUDY_PIXEL_PERCENTAGE", aoi, dates
    )
