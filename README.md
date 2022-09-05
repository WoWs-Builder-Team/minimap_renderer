## Minimap Renderer

![Tests](https://github.com/WoWs-Builder-Team/minimap_renderer/actions/workflows/tests.yml/badge.svg)

Minimap Renderer parses World of Warships replays to create a timelapse video that resembles the in-game minimap.

![enter image description here](images/minimap.gif)

### Installation
1. Get Python 3.10 or higher

	A virtual environment can be created with `python3.10 -m venv venv`.

2. Clone the repository
	```
	git clone https://github.com/WoWs-Builder-Team/minimap_renderer.git
	```
3. Install the package.
	```
	cd minimap_renderer
	pip install -e .
	```
4. You're set!

### Usage
Replays can be parsed with `render.py`. The full usage is:
```
render.py --replay <replay_path>
```
This will create a video file of your replay.

### License

This project is licensed under the GNU AGPLv3 License.

### Credits and Links

- This project is maintained by `@notyourfather#7816` and `@Trackpad#1234`.

- However, it would not have been possible without Monstrofil's [replays_unpack](https://github.com/Monstrofil/replays_unpack)!

- A minimal Discord bot wrapper is available [here](https://github.com/WoWs-Builder-Team/minimap_renderer_bot).

- One with additional features is available [here](https://github.com/padtrack/track).