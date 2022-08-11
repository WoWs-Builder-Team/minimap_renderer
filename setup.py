from setuptools import setup, find_packages


setup(
    name="Minimap Renderer",
    version="0.0.1",
    author="notyourfather, trackpad",
    description=(
        "Minimap Renderer parses World of Warships replays to create a "
        "timelapse video that resembles the in-game minimap."
    ),
    license="AGPL 3.0",
    keywords="minimap renderer worldofwarships wows replay",
    url="https://github.com/WoWs-Builder-Team/minimap_renderer",
    packages=find_packages(),
    scripts=[
        "create_data.py",
        "render_dual.py",
        "render.py",
        "replay_parser.py",
    ],
)
