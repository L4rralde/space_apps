import os

import pandas as pd
import numpy as np
from obspy import read

DATA_DIR = f"{os.environ['SPACE']}/data/lunar/training/data/S12_GradeA/"
CATALOGS_PATH = f"{os.environ['SPACE']}/data/lunar/training/catalogs/"
CATALOG_PATH = f"{os.environ['SPACE']}/data/lunar/training/catalogs/apollo12_catalog_GradeA_final.csv"


def get_data() -> pd.DataFrame:
    fpath = f"{os.environ['SPACE']}/data/lunar/training/catalogs/apollo12_catalog_GradeA_final.csv"
    cat = pd.read_csv(fpath)
    test_filename = cat.iloc[6].filename
    csv_file = f'{DATA_DIR}/{test_filename}.csv'
    df = pd.read_csv(csv_file).sort_values(by=['time_rel(sec)'])

    return (df['time_rel(sec)'], df['velocity(m/s)'])
