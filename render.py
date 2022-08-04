import pickle

from renderer.render import Renderer

if __name__ == "__main__":
    with open("data.dat", "rb") as f:
        Renderer(pickle.load(f)).start()
