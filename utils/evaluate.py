import sys

import pandas as pd
import numpy as np

from utils import CATALOGS_PATH, CATALOG_PATH


K = 20

def calc_metrics(model_result, ground_truth) -> None:
    model_result["result"] =  model_result["time_rel(sec)"]
    model_result["truth"] =  ground_truth["time_rel(sec)"]
    model_result["true_positive"] = abs(model_result["result"] - model_result["truth"]) <= K
    model_result["false_positive"] = abs(model_result["result"] - model_result["truth"]) > K
    model_result["true_negative"] = model_result['result'].isna() &\
                                    model_result['truth'].isna()
    model_result["false_negative"] = model_result['result'].isna() &\
                                    model_result['truth'].notna()

def main() -> None:
    ground_truth = pd.read_csv(CATALOG_PATH)
    model_result = pd.read_csv(f"{CATALOGS_PATH}/fake.csv")
    calc_metrics(model_result, ground_truth)
    n = len(model_result.index) - 1.0
    tp = model_result["true_positive"].sum()/n
    fp = model_result["false_positive"].sum()/n
    tn = model_result["true_negative"].sum()/n
    fn = model_result["false_negative"].sum()/n
    accuracy = (model_result["true_positive"].sum() + model_result["true_negative"].sum())/n
    print(f"True Positive ratio = {tp}")
    print(f"False Positive ratio = {fp}")
    print(f"True Negative ratio = {tn}")
    print(f"False Positive ratio = {fn}")
    print(f"Accuracy = {accuracy}")

if __name__ == '__main__':
    main()
