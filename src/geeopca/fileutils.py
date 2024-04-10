import json
import geopandas as gpd
import matplotlib.pyplot as plt


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


def save_plot(figure: plt.Figure, filename: str = None) -> None:
    filename = filename or "plot.png"
    figure.savefig(filename)


def load_json_data(jsonfile) -> dict[str, list[str]]:
    with open(jsonfile, "r") as fh:
        return json.load(fh)
