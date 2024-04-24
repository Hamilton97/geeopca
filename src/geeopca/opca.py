from typing import Any
import ee


class OpcaCalculator:
    def compute(self, image: ee.Image) -> ee.Image:
        pc_names = self.get_names("pc_", ee.List.sequence(1, image.bandNames().size()))
        array_image = image.toArray()

        covariance = array_image.reduceRegion(
            **{"reducer": ee.Reducer.covariance(), "maxPixels": 1e13}
        )

        covariance_array = ee.Array(covariance.get("array"))

        eigens = covariance_array.eigen()
        eigen_vec = eigens.slice(1, 1)
        principal_compoents = ee.Image(eigen_vec).matrixMultiply(array_image.toArray(1))
        return principal_compoents.arrayProject([0]).arrayFlatten([pc_names])

    @staticmethod
    def get_names(prefix: str, sequence: list[int] | ee.List):
        return ee.List(sequence).map(
            lambda x: ee.String(prefix).cat(ee.Number(x).int())
        )


def get_opca_min_max(pc_image: ee.Image) -> Any:
    # Define a region of interest, which could be the whole image
    roi = pc_image.geometry()

    # Use the reducer to get the min and max
    stats = pc_image.reduceRegion(
        reducer=ee.Reducer.minMax(), geometry=roi, bestEffort=True
    )
    return stats
