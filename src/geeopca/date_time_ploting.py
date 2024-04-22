from geeopca.plots import date_time_scatter_plot
from geeopca.datautils import DateRanger


def make_s2_dt_plots(aoi, start, end):
    from geeopca.rsd import Sentinel2TOA
    
    ranges = DateRanger(start, end)

    ds = None
    for dt_range in ranges:
        start, end = dt_range
        if ds is None:
            ds = Sentinel2TOA(aoi, start, end)
            continue
        ds += Sentinel2TOA(aoi, start, end)
    
    df = ds.to_dataframe()
    fig = date_time_scatter_plot(df)
    return fig, df