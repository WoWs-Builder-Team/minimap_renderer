<div align="center">

# Minimap Renderer

**将《战舰世界》回放转换为清晰、流畅的小地图战斗视频**

[English](README_EN.md) · [问题反馈](https://github.com/In-dor/minimap_renderer/issues) · [原始项目](https://github.com/WoWs-Builder-Team/minimap_renderer)

[![Tests](https://github.com/In-dor/minimap_renderer/actions/workflows/tests.yml/badge.svg)](https://github.com/In-dor/minimap_renderer/actions/workflows/tests.yml)
[![Python 3.10](https://img.shields.io/badge/Python-3.10-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-2E7D32.svg)](LICENSE)
[![Maintained](https://img.shields.io/badge/状态-持续维护-00A86B.svg)](https://github.com/In-dor/minimap_renderer)

![Minimap Renderer 演示](images/minimap.gif)

</div>

> [!IMPORTANT]
> [WoWs-Builder-Team/minimap_renderer](https://github.com/WoWs-Builder-Team/minimap_renderer) 已归档，不再维护。当前持续维护的版本是 **[In-dor/minimap_renderer](https://github.com/In-dor/minimap_renderer)**。请在本仓库安装、提交问题和获取更新。

## 功能亮点

- **原生高分辨率绘制**：直接在 `1920x1200` 目标画布上渲染，不依赖后期放大，文字和图标更加清晰。
- **原生时间插值**：对舰船位置、航向、飞机、炮弹和鱼雷生成中间状态，默认输出流畅的 `60 FPS` 视频。
- **完整战斗信息**：显示舰船、血量、消耗品、占领点、比分、伤害、勋带、击杀、聊天和战斗结果。
- **高效渲染流水线**：引入帧缓冲内存池复用、舰船旋转与状态 LRU 缓存、紧凑包围盒快速 Alpha 合成，并并行执行绘制、帧序列化与 FFmpeg 硬件编码。
- **兼容多种补帧方式**：除推荐的 `native` 外，仍可使用 `blend`、`duplicate` 和 `motion`。
- **自动导出配置信息**：渲染视频时同时生成玩家配装链接 JSON 文件。
- **2.4K 战报全景长图**：默认在渲染视频时同步生成对齐 WG 战后结算的 2.4K 超高清战绩战报长图（包含基础经验与原始裸经验双列对照、战舰击沉与防空战机击落、完整局内通讯记录、车队组队联动标识及主炮弹药明细）。

## 快速开始

### 环境要求

- Python `3.10`
- Windows 或 Linux
- 有效的《战舰世界》`.wowsreplay` 回放文件

项目通过 `imageio-ffmpeg` 提供视频编码能力，正常安装后通常不需要单独配置 FFmpeg。

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

## 使用方法

使用默认配置渲染一场回放：

```bash
python -m render --replay "路径/到/回放文件.wowsreplay"
```

Windows 示例：

```bat
python -m render --replay "F:\Replays\20260713_165525_PRSB510-Slava_54_Faroe.wowsreplay"
```

默认配置为 `1920x1200`、`60 FPS`、`15x` 速度、质量 `8` 和原生插值。生成文件位于回放文件旁边：

```text
回放文件.mp4
回放文件-builds.json
回放文件-report.png
```

查看完整命令帮助：

```bash
python -m render --help
```

## 命令参数

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

| 参数              |      默认值 | 说明                                                                                        |
| ----------------- | ----------: | ------------------------------------------------------------------------------------------- |
| `--replay`        |        必填 | `.wowsreplay` 文件路径                                                                      |
| `--fps`           |        `60` | 输出视频帧率；数值越高越流畅，渲染帧数也越多                                                |
| `--speed`         |        `15` | 延时播放倍速；例如 `15` 表示约 15 倍速                                                      |
| `--resolution`    | `1920x1200` | 原生渲染分辨率，必须保持 `1360:850`（即 `8:5`）布局比例                                     |
| `--quality`       |         `8` | 编码质量，范围 `1-10`；数值越高，画质和文件体积通常越高                                     |
| `--interpolation` |    `native` | 帧生成方式，见下表                                                                          |
| `--codec`         |      `h264` | 视频编码格式：兼容性较好的 `h264`、压缩率更高的 `h265` 或 `av1`                             |
| `--encoder`       |      `auto` | 自动实测并使用可用的硬件编码器，均不可用时回退 CPU；也可指定 `cpu`、`nvenc`、`qsv`、`vaapi` 或 `amf` |
| `--no-report`     |     `False` | 禁用自动生成 2.4K 战报长图                                                                  |
| `--report-only`   |     `False` | 仅生成 2.4K 战报长图（跳过小地图视频逐帧渲染，秒级出图）                                   |
| `--report-path`   |      `None` | 自定义战报长图输出路径（默认保存在回放同级目录下 `*-report.png`）                           |

### 视频编码器

`--codec` 决定视频格式，`--encoder` 决定使用 CPU 或哪一种硬件后端。`auto` 会针对所选格式依次实际测试 NVIDIA NVENC、Intel Quick Sync、Linux VAAPI 和 AMD AMF，而不是只检查 FFmpeg 是否列出了编码器。硬件或驱动不可用时会自动回退对应的 CPU 编码器，并在日志中显示最终选择。

| 格式   | CPU 回退     | 特点                                           |
| ------ | ------------ | ---------------------------------------------- |
| `h264` | `libx264`    | 播放器和网页兼容性最好，默认推荐               |
| `h265` | `libx265`    | 同等画质下文件通常更小，但部分浏览器不支持     |
| `av1`  | `libaom-av1` | 压缩效率较高；CPU 编码很慢，需要较新的播放环境 |

显式指定 `--encoder qsv` 或 `--encoder vaapi` 时，如果该格式的编码器无法初始化，程序会直接报错，不会静默改用其他设备。Intel Linux NAS 建议保留 `--encoder auto`：QSV 初始化失败后会继续测试 VAAPI，最后才回退 CPU。

Docker 或 LXC 环境需要映射 `/dev/dri/renderD128`、授予容器进程 `render` 组权限，并安装 Intel 媒体驱动。默认 VAAPI 设备是 `/dev/dri/renderD128`，可通过 `VAAPI_DEVICE` 修改。若 imageio 捆绑的 FFmpeg 不含 VAAPI，请设置 `IMAGEIO_FFMPEG_EXE=/usr/bin/ffmpeg` 使用容器内的系统 FFmpeg。硬件编码主要降低编码阶段的 CPU 占用，Python/Pillow 图层绘制仍由 CPU 完成。

### 插值模式

| 模式        | 特点                                                 | 建议用途       |
| ----------- | ---------------------------------------------------- | -------------- |
| `native`    | 在渲染器中计算物体中间状态；移动清晰，无整帧混合重影 | **默认推荐**   |
| `blend`     | FFmpeg 混合相邻帧；速度较快，但移动物体可能出现重影  | 兼容旧输出风格 |
| `duplicate` | 复制源帧达到目标帧率；最快，但运动不够连贯           | 更看重速度时   |
| `motion`    | FFmpeg 运动补偿；计算成本很高，复杂场景可能产生伪影  | 实验性用途     |

`native` 模式要求 `--fps` 不低于 `--speed`。例如 `--fps 60 --speed 15` 每个源时间间隔通常会生成约四个输出帧。

## 推荐配置

平衡清晰度、流畅度和速度：

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

更快、更小的输出：

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

## 战报长图生成

渲染器默认在输出视频时自动生成一份 2.4K 超高清战报长图（`*-report.png`）。

如果只需要快速复盘战绩或导出图片分享，无需花费时间渲染完整的小地图延时视频，可以使用 `--report-only` 参数：

```bash
python -m render --replay "battle.wowsreplay" --report-only
```

也可以直接调用独立的快捷工具脚本：

```bash
python tools/generate_battle_report.py "battle.wowsreplay"
```

战报内容亮点：
- **官方真值结算**：自动从回放协议末尾的 WG 战后结算包（Packet 0x22）直接提取全场 24 人的官方真值造成伤害、点亮伤害与潜在伤害。
- **双经验列呈现**：同时展示含 1.5x 胜利加成后的【基础经验】（与游戏内记分榜 1:1 对齐并作为排序依据）以及未乘算系数的【原始裸经验】。
- **防空与击沉双标**：独立呈现全场战舰击沉与击落战机数量。
- **全量局内通讯**：完整呈现整场文字聊天，根据频道与发言人阵营智能着色（分队金黄、友方薄荷绿、敌方浅珊瑚红）。
- **组队联动标识**：精准还原车队分队编号徽章与队友专属视觉高亮。

## 性能参考

以下数据来自同一场 15.5 版本回放，配置为 `1920x1200 / 60 FPS / 15x / quality 8 / native`：

| 项目           |      优化前 |       当前版本 |
| -------------- | ----------: | -------------: |
| 正常战斗帧吞吐 | `55.85 FPS` |   `118.89 FPS` |
| 完整命令耗时   |  `50.18 秒` |     `24.17 秒` |
| 相对速度       |     `1.00x` | **约 `2.08x`** |

实际速度取决于 CPU、内存带宽、回放长度、战斗复杂度和后台负载。当前流水线主要利用多个阶段并行工作，而有状态的战斗图层仍按时间顺序绘制，以保证结果正确。

## 兼容性说明

渲染器包含针对多个游戏版本的适配图层，目前**已持续跟进适配至最新的 `15.8.0` 版本**，并向下兼容历史版本回放以及行动模式等特殊对局类型消耗品。新游戏版本发布时可能会修改回放数据结构，因此无法保证尚未适配的版本能够立即解析或完整显示。

遇到问题时，请提交 [Issue](https://github.com/In-dor/minimap_renderer/issues)，并附上：

- 游戏版本和服务器区域
- 完整错误日志
- 实际使用的命令
- 可用于复现问题的回放文件（如方便提供）

## 从源码开发

```bash
git clone https://github.com/In-dor/minimap_renderer.git
cd minimap_renderer
python -m venv .venv
```

Windows：

```bat
.venv\Scripts\activate
pip install -e ".[testing]"
pytest
```

Linux：

```bash
source .venv/bin/activate
pip install -e ".[testing]"
pytest
```

## 项目沿革与致谢

本仓库复刻自已归档的 [WoWs-Builder-Team/minimap_renderer](https://github.com/WoWs-Builder-Team/minimap_renderer)，并在其基础上继续适配游戏版本、修复问题和改进渲染质量与性能。

感谢原项目维护者 `notyourfather`、`Trackpad` 及所有历史贡献者。回放解析相关工作也离不开 Monstrofil 的 [replays_unpack](https://github.com/Monstrofil/replays_unpack)。

## 许可证

本项目基于 [GNU Affero General Public License v3.0](LICENSE) 发布。
