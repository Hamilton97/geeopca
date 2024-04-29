from configparser import ConfigParser


def run():
    config = ConfigParser()
    
    # add date plot params
    config['opca.dateplots'] = {
        'dataset': 's2',
        'spatialfile': '<YOUR PATH HERE>',
        'output_dir': ".",
        'plot_name': "figure.png",
        'table_name': "table.csv",
        'start_date': 'YYYY-MM-dd',
        'end_date': 'YYYY-MM-dd'
    }
    
    config['opca.compute'] = {
        'table': "",
        'target_year': "",
        'selectors': "None",
        'NDVI': "False",
        'NDWI': "False",
        'SWM': "False",
        'spatialfile': "",
        'cloud_bucket': ""
    }
    
    with open("conf.ini", 'w') as fh:
        config.write(fh)

    return 0

if __name__ == '__main__':
    run()