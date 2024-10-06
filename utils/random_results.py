import random
import os

import pandas as pd
import numpy as np

from utils import DATA_DIR, CATALOGS_PATH, CATALOG_PATH


def new_value(row: object) -> object:
    filename = f"{DATA_DIR}/{row["filename"]}.csv"
    time_series = pd.read_csv(filename)
    completely_random = random.randint(0, int(np.max(time_series["time_rel(sec)"])))
    sel = random.random()
    if(sel < 0.05):
        return np.nan
    if(sel < 0.15):
        return completely_random
    displacement = 10 * (1 - 2*random.random())
    return float(int(row["time_rel(sec)"] +  displacement))


def main() -> None:
    df = pd.read_csv(CATALOG_PATH)
    df["new_resutl"] = df.apply(lambda row: new_value(row), axis=1)
    df["time_rel(sec)"] = df["new_resutl"]
    df = df.drop(columns=["new_resutl"])
    df.to_csv(f"{CATALOGS_PATH}/fake.csv")

if __name__ == '__main__':
    main()
