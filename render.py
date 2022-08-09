import pickle
import timeit

from renderer.render import Renderer

setup = """
from renderer.render import Renderer
import pickle
"""
code = """
with open("data.dat", "rb") as f:
    Renderer(pickle.load(f)).start()
"""

if __name__ == "__main__":
    with open("data.dat", "rb") as f:
        Renderer(pickle.load(f)).start(
            "minimap.mp4", enable_chat=True, anon=True
        )
    # result = timeit.timeit(code, setup, number=10)
    # print(result)
