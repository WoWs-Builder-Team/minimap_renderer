import pickle

from renderer import get_renderer
import time

if __name__ == "__main__":
    with open("data.dat", "rb") as f:
        a = time.perf_counter()
        get_renderer("0_11_6")(pickle.load(f)).start()
        b = time.perf_counter()
        print(b - a)
