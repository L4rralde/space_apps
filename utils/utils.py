import pandas as pd
import numpy as np
from obspy import read

data_directory = '../data/lunar/training/data/S12_GradeA/'

def get_data() -> pd.DataFrame:
    fpath = "../data/lunar/training/catalogs/apollo12_catalog_GradeA_final.csv"
    cat = pd.read_csv(fpath)
    test_filename = cat.iloc[6].filename
    csv_file = f'{data_directory}{test_filename}.csv'
    df = pd.read_csv(csv_file).sort_values(by=['time_rel(sec)'])

    return (df['time_rel(sec)'], df['velocity(m/s)'])
