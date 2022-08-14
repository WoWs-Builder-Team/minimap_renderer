import pickle

from renderer.render import Renderer


def progress(a):
    print(a)


if __name__ == "__main__":
    with open("data.dat", "rb") as f:
        Renderer(
            pickle.load(f), logs=True, enable_chat=True, use_tqdm=False
        ).start("minimap.mp4", progress_cb=progress)
