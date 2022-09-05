
## Minimap Renderer

![Tests](https://github.com/WoWs-Builder-Team/minimap_renderer/actions/workflows/tests.yml/badge.svg)

Minimap Renderer parses World of Warships replays to create a timelapse video that resembles the in-game minimap.

![enter image description here](images/minimap.gif)

### Installation
1. Install Python 3.10
2. Clone this repository, wait for it to finish and `cd` into it.
	```
	cd minimap_renderer
	```
3. Create a Python virtual environment.
   - Linux
	 
	```
	    . venv/bin/activate
	```
	
   - Windows
	```
	    . venv/bin/activate
	```
   - You should now see `(venv)` at the start of the command prompt.
	
4. Install the renderer package. To install the renderer package use this command.
	```
	pip install -e .
	```
5. You're all set.

### Usage
Replays can be parsed with `render.py`. The full usage is:
```
python render.py --replay <replay_path>
```
This will create a `.mp4` file from your replay file.

Since the renderer is installed to a virtual environment, you need to activate it  once before you render. Once activated, you can render any replay file as long as it is a 0.11.6, 0.11.7 replay file.

### License

This project is licensed under the GNU AGPLv3 License.

### Credits and Links

- This project is maintained by `@notyourfather#7816` and `@Trackpad#1234`.

- However, it would not have been possible without Monstrofil's [replays_unpack](https://github.com/Monstrofil/replays_unpack)!

- A minimal Discord bot wrapper is available [here](https://github.com/WoWs-Builder-Team/minimap_renderer_bot).

- One with additional features is available [here](https://github.com/padtrack/track).
