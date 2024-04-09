import ee


def pca(image: ee.Image, bands: list[str]) -> ee.Image:
    pca_bands = [f"pc{_}" for _ in range(1, len(bands) + 1)]
    array_image = image.select(bands).toArray()

    covariance = array_image.reduceRegion(
        **{"reducer": ee.Reducer.covariance(), "maxPixels": 1e13}
    )

    covariance_array = ee.Array(covariance.get("array"))

    eigens = covariance_array.eigen()
    eigen_vec = eigens.slice(1, 1)
    principal_compoents = ee.Image(eigen_vec).matrixMultiply(array_image.toArray(1))

    pc_image = principal_compoents.arrayProject([0]).arrayFlatten([pca_bands])

    return pc_image


def temporal_pca(data: list[ee.Image], bands: list[str]):
    return [pca(image, bands) for image in data]
