<div align="center">

# Minimap Renderer

**Turn World of Warships replays into crisp, smooth minimap battle videos**

[简体中文](README.md) · [Report an issue](https://github.com/In-dor/minimap_renderer/issues) · [Original project](https://github.com/WoWs-Builder-Team/minimap_renderer)

[![Tests](https://github.com/In-dor/minimap_renderer/actions/workflows/tests.yml/badge.svg)](https://github.com/In-dor/minimap_renderer/actions/workflows/tests.yml)
[![Python 3.10](https://img.shields.io/badge/Python-3.10-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-2E7D32.svg)](LICENSE)
[![Maintained](https://img.shields.io/badge/status-maintained-00A86B.svg)](https://github.com/In-dor/minimap_renderer)

![Minimap Renderer demo](images/minimap.gif)

</div>

> [!IMPORTANT]
> [WoWs-Builder-Team/minimap_renderer](https://github.com/WoWs-Builder-Team/minimap_renderer) has been archived and is no longer maintained. The actively maintained version is **[In-dor/minimap_renderer](https://github.com/In-dor/minimap_renderer)**. Install updates and report issues here.

## Highlights

- **Native high-resolution rendering**: draws directly at `1920x1200` instead of upscaling afterward, keeping text and icons sharp.
- **Native temporal interpolation**: generates intermediate states for ship position and heading, aircraft, shells, and torpedoes for smooth `60 FPS` output by default.
- **Detailed battle information**: renders ships, health, consumables, capture points, scores, damage, ribbons, frags, chat, and battle results.
- **Efficient rendering pipeline**: features frame buffer memory reuse pools, ship rotation and status LRU caches, compact bounding-box alpha compositing, and overlapped drawing, frame serialization, and FFmpeg hardware encoding.
- **Multiple interpolation modes**: supports `native`, `blend`, `duplicate`, and `motion`.
- **Build export**: writes a JSON file containing player build links alongside the video.
- **2.4K Battle Report Infographic**: automatically generates a comprehensive 2.4K post-battle scoreboard long card by default, featuring base XP & raw unmultiplied XP, ship frags & planes downed, full in-game communication logs with team-color coding, division badges, and weapon damage breakdown.

## Quick Start

### Requirements

- Python `3.10`
- Windows or Linux
- A valid World of Warships `.wowsreplay` file

Video encoding is provided through `imageio-ffmpeg`, so a separate FFmpeg setup is usually unnecessary after a normal installation.

### Windows

```bat
py -3.10 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install --upgrade --force-reinstall git+https://github.com/In-dor/minimap_renderer.git
```

### Linux

```bash
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install --upgrade --force-reinstall git+https://github.com/In-dor/minimap_renderer.git
```

## Usage

Render a replay with the default settings:

```bash
python -m render --replay "path/to/battle.wowsreplay"
```

Windows example:

```bat
python -m render --replay "F:\Replays\20260713_165525_PRSB510-Slava_54_Faroe.wowsreplay"
```

The defaults are `1920x1200`, `60 FPS`, `15x` speed, quality `8`, and native interpolation. Output files are created next to the replay:

```text
battle.mp4
battle-builds.json
battle-report.png
```

Show the complete command help:

```bash
python -m render --help
```

## Command Options

```text
python -m render --replay REPLAY
                 [--fps FPS]
                 [--speed SPEED]
                 [--resolution WIDTHxHEIGHT]
                 [--quality 1-10]
                 [--interpolation {native,blend,motion,duplicate}]
                 [--codec {h264,h265,av1}]
                 [--encoder {auto,cpu,nvenc,qsv,vaapi,amf}]
                 [--no-report]
                 [--report-only]
                 [--report-path REPORT_PATH]
```

| Option            |     Default | Description                                                                                                                |
| ----------------- | ----------: | -------------------------------------------------------------------------------------------------------------------------- |
| `--replay`        |    required | Path to the `.wowsreplay` file                                                                                             |
| `--fps`           |        `60` | Output frame rate; higher values produce smoother video and more rendered frames                                           |
| `--speed`         |        `15` | Timelapse playback multiplier; `15` means approximately 15x speed                                                          |
| `--resolution`    | `1920x1200` | Native render resolution; it must preserve the `1360:850` (`8:5`) layout ratio                                             |
| `--quality`       |         `8` | Encoding quality from `1-10`; higher values generally increase quality and file size                                       |
| `--interpolation` |    `native` | Frame generation mode, described below                                                                                     |
| `--codec`         |      `h264` | Video format: broadly compatible `h264`, more efficient `h265`, or `av1`                                                   |
| `--encoder`       |      `auto` | Probes available hardware encoders and falls back to CPU; `cpu`, `nvenc`, `qsv`, `vaapi`, and `amf` can also be selected explicitly |
| `--no-report`     |     `False` | Disable automatic 2.4K battle report generation                                                                            |
| `--report-only`   |     `False` | Generate 2.4K battle report infographic only (skips timelapse video rendering, fast ~1s output)                           |
| `--report-path`   |      `None` | Custom output path for the battle report image (defaults to `<replay_stem>-report.png`)                                    |

### Video Encoders

`--codec` selects the video format, while `--encoder` selects CPU or a hardware backend. For the selected format, `auto` performs a real encoding test with NVIDIA NVENC, Intel Quick Sync, Linux VAAPI, and AMD AMF in that order instead of merely checking whether FFmpeg lists an encoder. It falls back to the corresponding CPU encoder when the hardware or driver is unavailable, and logs the result.

| Format | CPU fallback | Characteristics                                                                       |
| ------ | ------------ | ------------------------------------------------------------------------------------- |
| `h264` | `libx264`    | Best player and browser compatibility; recommended default                            |
| `h265` | `libx265`    | Usually smaller at similar quality, but unsupported by some browsers                  |
| `av1`  | `libaom-av1` | High compression efficiency; CPU encoding is slow and playback support must be recent |

When `--encoder qsv` or `--encoder vaapi` is selected explicitly, initialization failure for that format is reported instead of silently switching devices. Intel Linux NAS systems should normally retain `--encoder auto`: when QSV initialization fails, the renderer tests VAAPI before falling back to CPU.

Docker and LXC deployments must expose `/dev/dri/renderD128`, grant the container process membership in the `render` group, and install the Intel media driver. The default VAAPI device is `/dev/dri/renderD128` and can be changed with `VAAPI_DEVICE`. If imageio's bundled FFmpeg lacks VAAPI, set `IMAGEIO_FFMPEG_EXE=/usr/bin/ffmpeg` to use the container's system FFmpeg. Hardware encoding primarily reduces CPU load during compression; Python/Pillow layer rendering remains CPU-bound.

### Interpolation Modes

| Mode        | Behavior                                                                                    | Recommended use                 |
| ----------- | ------------------------------------------------------------------------------------------- | ------------------------------- |
| `native`    | Interpolates object states in the renderer; motion stays sharp without whole-frame blending | **Recommended default**         |
| `blend`     | Uses FFmpeg to blend adjacent frames; fast, but moving objects may show ghosting            | Compatibility with older output |
| `duplicate` | Repeats source frames to reach the output rate; fastest, but motion is less fluid           | Maximum speed                   |
| `motion`    | Uses FFmpeg motion compensation; very expensive and may create artifacts in complex scenes  | Experimental use                |

In `native` mode, `--fps` must not be lower than `--speed`. With `--fps 60 --speed 15`, each source interval usually produces about four output frames.

## Recommended Settings

Balanced clarity, smoothness, and rendering speed:

```bash
python -m render --replay "battle.wowsreplay" \
  --fps 60 \
  --speed 15 \
  --resolution 1920x1200 \
  --quality 8 \
  --interpolation native \
  --codec h264 \
  --encoder auto
```

Faster and smaller output:

```bash
python -m render --replay "battle.wowsreplay" \
  --fps 30 \
  --speed 15 \
  --resolution 1360x850 \
  --quality 7 \
  --interpolation native \
  --codec h265 \
  --encoder auto
```

## Battle Report Infographic Generation

The renderer automatically creates a 2.4K Ultra-HD battle report long card (`*-report.png`) by default when producing a video.

If you only need to inspect results or export the scoreboard infographic without spending time rendering the full timelapse video, use `--report-only`:

```bash
python -m render --replay "battle.wowsreplay" --report-only
```

Or invoke the standalone utility script directly:

```bash
python tools/generate_battle_report.py "battle.wowsreplay"
```

Report highlights:
- **Official WG Settlement Values**: Directly extracts true post-battle damage dealt, spotting damage, and potential damage for all 24 players from Packet 0x22 (`playersPublicInfo`).
- **Dual XP Presentation**: Side-by-side display of in-game Base XP (with 1.5x victory bonus, matching client scoreboard ordering) and pure unmultiplied Raw Base XP.
- **AA & Frags Tracking**: Independent columns for ship kills and aircraft shot down.
- **Full In-Game Chat Log**: Renders all match messages with authentic team/division color coding.
- **Division Squad Links**: Displays squad badges and dedicated color-coding for division mates.

## Performance Reference

The following results use the same game 15.5 replay at `1920x1200 / 60 FPS / 15x / quality 8 / native`:

| Metric                         | Before optimization |   Current version |
| ------------------------------ | ------------------: | ----------------: |
| Normal battle-frame throughput |         `55.85 FPS` |      `118.89 FPS` |
| Full command time              |           `50.18 s` |         `24.17 s` |
| Relative speed                 |             `1.00x` | **about `2.08x`** |

Actual performance depends on CPU speed, memory bandwidth, replay length, battle complexity, and background load. The current pipeline overlaps independent stages while preserving strict ordering for stateful battle layers.

## Compatibility

The renderer contains version-specific adapters for multiple game releases and is **currently maintained up to version `15.7.0`**, with backward compatibility for earlier replays and support for Operation mode consumables. New game versions may change the replay format, so versions that have not been adapted yet are not guaranteed to parse or render completely.

When reporting an [issue](https://github.com/In-dor/minimap_renderer/issues), include:

- Game version and server region
- Complete error output
- The exact command used
- A replay that reproduces the problem, when possible

## Development Setup

```bash
git clone https://github.com/In-dor/minimap_renderer.git
cd minimap_renderer
python -m venv .venv
```

Windows:

```bat
.venv\Scripts\activate
pip install -e ".[testing]"
pytest
```

Linux:

```bash
source .venv/bin/activate
pip install -e ".[testing]"
pytest
```

## History and Credits

This repository is a maintained fork of the archived [WoWs-Builder-Team/minimap_renderer](https://github.com/WoWs-Builder-Team/minimap_renderer). It continues game-version support, bug fixes, rendering-quality improvements, and performance work.

Thanks to the original maintainers `notyourfather`, `Trackpad`, and all previous contributors. Replay parsing also builds on Monstrofil's [replays_unpack](https://github.com/Monstrofil/replays_unpack).

## License

This project is distributed under the [GNU Affero General Public License v3.0](LICENSE).
