import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

from geeopca.rsd import get_data
from geeopca.plots import date_time_scatter_plot
from geeopca.datautils import DateRanger, localize_utc


def make_date_time_plots(level: int, aoi: str, start: str, end: str) ->tuple[plt.Figure, gpd.GeoDataFrame]:
    
    datasets = {
        1: {'id': 'COPERNICUS/S2_HARMONIZED', 'cloud': 'CLOUDY_PIXEL_PERCENTAGE'}
    }
    
    data_level = datasets.get(level, None)
    if data_level is None:
        raise ValueError("Not a valid processing level")
    
    id = data_level.get('id')
    property = data_level.get('cloud')
    
    gdfs = [
        get_data(id, aoi, t1, t2, property) for t1, t2 in DateRanger(start, end)
    ]
    
    gdf = pd.concat(gdfs)

    # localize the UTC column
    gdf = localize_utc(gdf)

    fig = date_time_scatter_plot(gdf)
    return fig, gdf

