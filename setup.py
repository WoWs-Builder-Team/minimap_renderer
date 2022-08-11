from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="minimap-renderer",
    version="0.0.1",
    author="notyourfather, trackpad",
    description=(
        "Minimap Renderer parses World of Warships replays to create a "
        "timelapse video that resembles the in-game minimap."
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="AGPL 3.0",
    keywords="minimap renderer worldofwarships wows replay",
    url="https://github.com/WoWs-Builder-Team/minimap_renderer",
    py_modules=["replay_parser"],
    packages=find_packages(),
    package_data={
        "": ["*.*", "*.png", "*.json", "*.ttf", "*.settings", "*def", "*.xml"],
        "renderer": ["*.png", "*.json", "*.ttf", "*.settings"],
        "replay_unpack": ["*.def", "*.xml"],
    },
    include_package_data=True,
    python_requires=">=3.10",
    scripts=[
        "create_data.py",
        "render_dual.py",
        "render.py",
        "replay_parser.py",
    ],
    install_requires=[
        "astroid==2.11.7",
        "autopep8==1.6.0",
        "black==22.6.0",
        "click==8.1.3",
        "colorama==0.4.5",
        "dill==0.3.5.1",
        "flake8==4.0.1",
        "imageio-ffmpeg==0.4.7",
        "isort==5.10.1",
        "lazy-object-proxy==1.7.1",
        "lxml==4.9.1",
        "mccabe==0.6.1",
        "mypy-extensions==0.4.3",
        "numpy==1.23.1",
        "pathspec==0.9.0",
        "Pillow==9.2.0",
        "platformdirs==2.5.2",
        "polib==1.1.1",
        "pycodestyle==2.8.0",
        "pycryptodomex==3.15.0",
        "pyflakes==2.4.0",
        "pylint==2.14.5",
        "toml==0.10.2",
        "tomli==2.0.1",
        "tomlkit==0.11.1",
        "tqdm==4.64.0",
        "typing_extensions==4.3.0",
        "wrapt==1.14.1",
    ],
)
