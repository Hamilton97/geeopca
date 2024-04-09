import geopandas as gpd
import pandas as pd

import matplotlib.pyplot as plt


def date_time_scatter_plot(df: gpd.GeoDataFrame | pd.DataFrame) -> plt.Figure:
    # Create a scatter plot
    fig, ax = plt.subplots()
    # Create a scatter plot on the axes

    ax.scatter(df["julian_date"], df["year"], alpha=0.5)

    # Set the limits for the x-axis and y-axis
    ax.set_xlim([1, 366])  # Julian dates range from 1 to 366
    ax.set_ylim(
        [df["year"].min() - 1, df["year"].max() + 1]
    )  # Years range from min to max year in the data

    # Set major tick marks every 50 on the x-axis and every 1 on the y-axis
    ax.set_xticks(range(0, 366, 50))
    ax.set_yticks(range(df["year"].min() - 1, df["year"].max() + 1, 1))

    ax.set_xlabel("Julian Day")
    ax.set_ylabel("Year")
    ax.set_title("Occurrence of Julian Days by Year")

    ax.grid(True)
    return fig


def save_plot(figure: plt.Figure, filename: str = None) -> None:
    filename = filename or "plot.png"
    figure.savefig(filename)
