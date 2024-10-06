import os
import sys
import glob

SPACE = os.environ["SPACE"]

sys.path.append(f"{SPACE}/model")
from codigo import Model


LUNAR_TEST_DIR = f"{SPACE}/data/lunar/test/data/"
MARS_TEST_DIR = f"{SPACE}/data/mars/test/data/"


def main():
    model = Model()
    mars_glob = glob.glob(f"{MARS_TEST_DIR}/*.mseed")
    for f in mars_glob:
        model.predict(f, percentile=65)
        model.plot()

if __name__ == '__main__':
    main()
