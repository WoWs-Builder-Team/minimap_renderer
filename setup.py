from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="minimap-renderer",
    version="0.0.3",
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
    packages=find_packages(exclude=["renderer_data*"]),
    include_package_data=True,
    python_requires=">=3.10",
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: GNU Affero General Public License v3",
    ],
    install_requires=[
        "black==22.6.0",
        "click==8.1.3",
        "colorama==0.4.5",
        "flake8==5.0.4",
        "imageio-ffmpeg==0.4.7",
        "lxml==4.9.1",
        "mccabe==0.7.0",
        "mypy-extensions==0.4.3",
        "numpy==1.23.2",
        "pathspec==0.9.0",
        "Pillow==9.2.0",
        "platformdirs==2.5.2",
        "polib==1.1.1",
        "pycodestyle==2.9.1",
        "pycryptodomex==3.15.0",
        "pyflakes==2.5.0",
        "tomli==2.0.1",
        "tqdm==4.64.0",
    ],
)
