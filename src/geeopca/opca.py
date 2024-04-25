from dataclasses import dataclass, InitVar
from typing import Any
import ee
import pandas as pd

from pprint import pprint

TABLE: str = r"C:\Users\rhamilton\github\geeopca\table.csv"
TARGET_YEAR: int = 2019
SELECTORS: list[str] | None = ['SWM']
NDVI: bool = False
NDWI: bool = False
SWM: bool = True


class Calculators:
    @staticmethod
    def compute_ndvi(nir, red):
        return lambda x: x.normalizedDifference([nir, red]).rename("NDVI")

    @staticmethod
    def compute_ndwi(green, nir):
        return lambda x: x.normalizedDifference([green, nir]).rename("NDWI")

    @staticmethod
    def sentinel_water_mask():
        return lambda x: x.expression('(b("B2") + b("B3")) / (b("B8") + b("B11"))').rename("SWM")
        


class Sentinel2Image:
    def __init__(self, arg: str) -> None:
        self.ee_image = ee.Image(arg).select("B.*")

    def add_ndvi(self):
        self.ee_image = self.ee_image.addBands(
            Calculators.compute_ndvi("B8", "B4")(self.ee_image).rename("NDVI")
        )
        return self
    
    def add_ndwi(self):
        self.ee_image = self.ee_image.addBands(
            Calculators.compute_ndwi('B3', 'B8')(self.ee_image)
        )
        return self

    def add_sentinel_water_mask(self):
        self.ee_image = self.ee_image.addBands(Calculators.sentinel_water_mask()(self.ee_image))
        return self


def prepare_images_dataset(args_array: list[str]):
    dataset = []
    for arg in args_array:
        if arg.startswith("COPERNICUS"):
            image = Sentinel2Image(arg)
        dataset.append(image)
    return dataset


def process_image_dataset(dataset: list[Sentinel2Image]):
    processed_images = []
    for image in dataset:
        if NDVI:
            image.add_ndvi()
        
        if NDWI:
            image.add_ndwi()
        
        if isinstance(image, Sentinel2Image) and SWM:
            image.add_sentinel_water_mask()

        processed_images.append(image)

    if SELECTORS is not None and len(SELECTORS) == 1:
        return [ee.Image.cat(*[x.ee_image.select(SELECTORS) for x in processed_images])]

    if SELECTORS is not None and len(SELECTORS) > 1:
        return [x.ee_image.select(SELECTORS) for x in processed_images]

    return [x.ee_image for x in processed_images]

def compute_pca(image: ee.Image) -> ee.Image:
    def get_names(prefix: str, sequence: list[int] | ee.List):
        return ee.List(sequence).map(
            lambda x: ee.String(prefix).cat(ee.Number(x).int())
        )

    pc_names = get_names("pc_", ee.List.sequence(1, image.bandNames().size()))
    array_image = image.toArray()

    covariance = array_image.reduceRegion(
        **{"reducer": ee.Reducer.covariance(), "maxPixels": 1e13}
    )

    covariance_array = ee.Array(covariance.get("array"))

    eigens = covariance_array.eigen()
    eigen_vec = eigens.slice(1, 1)
    principal_compoents = ee.Image(eigen_vec).matrixMultiply(array_image.toArray(1))
    return principal_compoents.arrayProject([0]).arrayFlatten([pc_names])


def get_opca_min_max(pc_image: ee.Image) -> Any:
    # Define a region of interest, which could be the whole image
    roi = pc_image.geometry()

    # Use the reducer to get the min and max
    stats = pc_image.reduceRegion(
        reducer=ee.Reducer.minMax(), geometry=roi, bestEffort=True
    )
    return stats


def main():
    df = pd.read_csv(TABLE)
    df = df[df["year"] == TARGET_YEAR]
    args_array: list[str] = df["syspath"].tolist()
    prepared_data = prepare_images_dataset(args_array)
    processed_data = process_image_dataset(prepared_data)
   
    for x in processed_data:
        print(x.bandNames().getInfo())
        pca_image = compute_pca(x).select('pc_[1-4]')
        pprint(pca_image.bandNames().getInfo())
        break
    


if __name__ == "__main__":
    ee.Initialize()
    main()
