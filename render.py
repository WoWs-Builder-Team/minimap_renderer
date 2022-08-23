import pickle

from renderer.render import Renderer


if __name__ == "__main__":
    with open("data.dat", "rb") as f:
        Renderer(
            pickle.load(f), logs=True, enable_chat=True, use_tqdm=True
        ).start("minimap.mp4")
