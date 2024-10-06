import os
import sys
import glob

import pandas as pd
import numpy as np

from codigo import Model


def main(args):
    path = os.path.realpath(args[1])
    model = Model()
    mseed_glob = glob.glob(f"{path}/*.mseed")
    d = dict()
    for mseed in mseed_glob:
        if "mars" in mseed:
            percentile = 65
        else:
            percentile = 95
        prediction = model.predict_pipeline(mseed, percentile = percentile)
        bname = ''.join(os.path.basename(mseed).split(".mseed")[0:-1])
        try:
            d[bname] = prediction.min_variance
        except:
            d[bname] = np.nan
    d_to_df = {
        "filename": d.keys(),
        "time_rel(sec)": d.values()
    }
    df = pd.DataFrame.from_dict(d_to_df)
    df.sort_values(by=["filename"], inplace=True)
    df.to_csv(f"{os.path.basename(os.path.realpath(args[1]))}.csv")


if __name__ == "__main__":
    main(sys.argv)
