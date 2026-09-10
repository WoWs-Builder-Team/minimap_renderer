import argparse
import os
import shutil
import subprocess
import logging
import sys
import glob
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_args():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(
        description="自动化更新 World of Warships 资源和代码"
    )
    parser.add_argument(
        "--wows-path", required=True, help="World of Warships 游戏安装根目录路径"
    )
    parser.add_argument(
        "--version", required=True, help="目标更新版本号 (例如: 14.8.0)"
    )
    return parser.parse_args()


def normalize_version(version):
    """
    将版本号转换为下划线格式 (例如: 14.8.0 -> 14_8_0)
    """
    return version.replace(".", "_")


def check_files(wows_path):
    """
    检查必要的文件是否存在
    """
    required_files = ["extract.py", "wowsunpack.exe"]
    for f in required_files:
        if not os.path.exists(f):
            logger.error(f"缺少必要文件: {f}")
            sys.exit(1)

    if not os.path.exists(wows_path):
        logger.error(f"游戏路径不存在: {wows_path}")
        sys.exit(1)

    logger.info("必要文件检查通过。")


def execute_extraction(wows_path):
    """
    执行资源提取
    """
    logger.info("开始执行资源提取...")

    # 复制工具到游戏目录
    try:
        shutil.copy("extract.py", wows_path)
        shutil.copy("wowsunpack.exe", wows_path)
        logger.info(f"已复制 extract.py 和 wowsunpack.exe 到 {wows_path}")
    except Exception as e:
        logger.error(f"复制工具失败: {e}")
        sys.exit(1)

    # 执行提取脚本
    # extract.py 默认提取最新 bin 版本
    cmd = [sys.executable, "extract.py"]
    try:
        subprocess.run(cmd, cwd=wows_path, check=True)
        logger.info("资源提取完成。")
    except subprocess.CalledProcessError as e:
        logger.error(f"提取脚本执行失败: {e}")
        sys.exit(1)


def move_resources(wows_path):
    """
    移动提取的关键资源到项目 resources 目录
    """
    logger.info("移动关键资源...")
    extract_root = os.path.join(wows_path, "res_extract")
    target_res_dir = "resources"

    if not os.path.exists(extract_root):
        logger.error(f"提取目录不存在: {extract_root}")
        sys.exit(1)

    os.makedirs(target_res_dir, exist_ok=True)

    def copy_gui_assets(src_rel, dst_rel, name):
        src = os.path.join(extract_root, *src_rel.split("/"))
        dst = os.path.join("src", "renderer", "resources", *dst_rel.split("/"))
        if os.path.exists(src):
            os.makedirs(dst, exist_ok=True)
            count = 0
            for root, dirs, files in os.walk(src):
                dirs[:] = [d for d in dirs if d != "subribbons"]
                rel_path = os.path.relpath(root, src)
                target_dir = os.path.join(dst, rel_path) if rel_path != "." else dst
                os.makedirs(target_dir, exist_ok=True)
                for file in files:
                    src_file = os.path.join(root, file)
                    dst_file = os.path.join(target_dir, file)
                    shutil.copy2(src_file, dst_file)
                    count += 1
            logger.info(f"已复制 {count} 个 {name} 到 {dst}")
        else:
            logger.warning(f"未找到 {name} 资源目录: {src}")

    # Copy ship bars
    copy_gui_assets("gui/ship_bars", "ship_bars", "ship_bars")
    # Copy consumables
    copy_gui_assets("gui/consumables", "consumables", "consumables")
    # Copy achievements
    copy_gui_assets("gui/achievements", "achievement_icons", "achievements")
    # Copy ribbons
    copy_gui_assets("gui/ribbons", "ribbon_icons", "ribbons")
    # Copy frag icons
    copy_gui_assets("gui/battle_hud/icon_frag", "frag_icons", "frag_icons")

    # 1. 移动 GameParams.data
    gp_src = os.path.join(extract_root, "content", "GameParams.data")
    if os.path.exists(gp_src):
        shutil.copy(gp_src, os.path.join(target_res_dir, "GameParams.data"))
        logger.info(f"已更新 GameParams.data")
    else:
        logger.warning(f"未找到 GameParams.data: {gp_src}")

    # 2. 移动 global.mo (只查找英文)
    # 路径结构通常为: texts/{locale}/LC_MESSAGES/global.mo
    texts_dir = os.path.join(extract_root, "texts")
    mo_src = None

    # 优先级: en
    locales_to_try = ["en"]

    if os.path.exists(texts_dir):
        # 尝试查找特定语言
        for locale in locales_to_try:
            candidate = os.path.join(texts_dir, locale, "LC_MESSAGES", "global.mo")
            if os.path.exists(candidate):
                mo_src = candidate
                logger.info(f"找到语言文件 ({locale}): {mo_src}")
                break

        # 如果没找到优先语言，尝试找任何存在的 global.mo
        if not mo_src:
            candidates = glob.glob(
                os.path.join(texts_dir, "*", "LC_MESSAGES", "global.mo")
            )
            if candidates:
                mo_src = candidates[0]
                logger.info(f"找到备选语言文件: {mo_src}")

    if mo_src and os.path.exists(mo_src):
        shutil.copy(mo_src, os.path.join(target_res_dir, "global.mo"))
        logger.info(f"已更新 global.mo")
    else:
        logger.warning(f"未找到 global.mo 在 {texts_dir}")


def update_maps(wows_path):
    """
    更新 maps/spaces
    """
    logger.info("更新 maps/spaces...")
    extract_spaces = os.path.join(wows_path, "res_extract", "spaces")
    target_spaces = os.path.join("maps", "spaces")

    if not os.path.exists(extract_spaces):
        logger.warning(f"未找到提取的 spaces 目录: {extract_spaces}")
        return

    # 使用 copytree 合并/覆盖
    # 注意：extract.py 提取了 minimap*.png 和 space.settings
    # 我们将这些文件复制到 maps/spaces，保留原有结构

    for root, dirs, files in os.walk(extract_spaces):
        rel_path = os.path.relpath(root, extract_spaces)
        target_dir = os.path.join(target_spaces, rel_path)

        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        for file in files:
            src_file = os.path.join(root, file)
            dst_file = os.path.join(target_dir, file)
            shutil.copy2(src_file, dst_file)

    logger.info("maps/spaces 更新完成。")


def update_replay_unpack(wows_path, version_normalized):
    """
    更新 src/replay_unpack
    1. 创建新版本目录
    2. 复制上一版本的 Python 脚本
    3. 复制新提取的 scripts (XML/DEF)
    """
    logger.info(f"更新 src/replay_unpack (版本: {version_normalized})...")

    base_path = os.path.join("src", "replay_unpack", "clients", "wows", "versions")
    new_version_path = os.path.join(base_path, version_normalized)

    # 查找上一版本
    versions = []
    if os.path.exists(base_path):
        for d in os.listdir(base_path):
            if os.path.isdir(os.path.join(base_path, d)) and d[0].isdigit():
                versions.append(d)

    versions.sort(key=lambda s: list(map(int, s.split("_"))))

    if not versions:
        logger.error("未找到任何现有版本，无法基准复制。")
        return

    last_version = versions[-1]
    if last_version == version_normalized and len(versions) > 1:
        last_version = versions[-2]
    logger.info(f"检测到上一版本为: {last_version}")

    if os.path.exists(new_version_path):
        logger.warning(f"目标版本目录已存在: {new_version_path}，将覆盖/合并")
    else:
        os.makedirs(new_version_path)

    # 复制上一版本的 Python 文件 (.py)
    if last_version != version_normalized:
        last_version_path = os.path.join(base_path, last_version)
        for file in os.listdir(last_version_path):
            if file.endswith(".py"):
                src_file = os.path.join(last_version_path, file)
                dst_file = os.path.join(new_version_path, file)
                shutil.copy2(src_file, dst_file)

    # 复制提取的 scripts
    extract_scripts = os.path.join(wows_path, "res_extract", "scripts")
    target_scripts = os.path.join(new_version_path, "scripts")

    if os.path.exists(extract_scripts):
        if os.path.exists(target_scripts):
            shutil.rmtree(target_scripts)
        shutil.copytree(extract_scripts, target_scripts)
        logger.info(f"已复制 scripts 到 {target_scripts}")
    else:
        logger.warning(f"未找到提取的 scripts 目录: {extract_scripts}")


def run_generators():
    """
    运行生成脚本: create_data.py 和 maps/spaces.py
    """
    logger.info("运行生成脚本...")

    # 运行 create_data.py
    try:
        logger.info("执行 create_data.py ...")
        subprocess.run([sys.executable, "create_data.py"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"create_data.py 执行失败: {e}")
        sys.exit(1)

    # 运行 maps/spaces.py
    try:
        logger.info("执行 maps/spaces.py ...")
        # maps/spaces.py 是作为一个脚本运行的
        subprocess.run([sys.executable, os.path.join("maps", "spaces.py")], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"maps/spaces.py 执行失败: {e}")
        sys.exit(1)


def update_renderer(version_normalized, wows_path=None):
    """
    更新 src/renderer
    1. 创建新版本资源目录
    2. 复制生成的 json 数据
    3. 更新全局 spaces
    """
    logger.info(f"更新 src/renderer (版本: {version_normalized})...")

    # 1. 创建新版本资源目录
    renderer_ver_path = os.path.join(
        "src", "renderer", "versions", version_normalized, "resources"
    )
    os.makedirs(renderer_ver_path, exist_ok=True)

    # 创建 __init__.py 以使其成为包
    Path(
        os.path.join("src", "renderer", "versions", version_normalized, "__init__.py")
    ).touch()
    Path(os.path.join(renderer_ver_path, "__init__.py")).touch()

    # 2. 应用生成的数据 (generated/ -> renderer_ver/resources/)
    generated_dir = "generated"
    json_files = glob.glob(os.path.join(generated_dir, "*.json"))

    if not json_files:
        logger.warning("在 generated/ 目录下未找到 JSON 文件。")

    for json_file in json_files:
        shutil.copy(json_file, renderer_ver_path)
        logger.info(f"已复制 {os.path.basename(json_file)}")

    # 3. 更新全局 src/renderer/resources/spaces
    # 数据源: maps/spaces (经过 maps/spaces.py 处理后)
    maps_spaces_dir = os.path.join("maps", "spaces")
    renderer_spaces_dir = os.path.join("src", "renderer", "resources", "spaces")

    logger.info("同步 maps/spaces 到 src/renderer/resources/spaces ...")

    if os.path.exists(renderer_spaces_dir):
        shutil.rmtree(renderer_spaces_dir)

    shutil.copytree(maps_spaces_dir, renderer_spaces_dir)
    logger.info("全局 spaces 更新完成")

    extract_root = os.path.join(wows_path, "res_extract") if wows_path else "res_extract"
    # Also need to get gui/ship_bars and update global resources
    ship_bars_src = os.path.join(extract_root, "gui", "ship_bars")
    ship_bars_dst = os.path.join("src", "renderer", "resources", "ship_bars")
    
    if os.path.exists(ship_bars_src):
        if not os.path.exists(ship_bars_dst):
            os.makedirs(ship_bars_dst)
        for root, _, files in os.walk(ship_bars_src):
            rel_path = os.path.relpath(root, ship_bars_src)
            target_dir = os.path.join(ship_bars_dst, rel_path)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            for file in files:
                src_file = os.path.join(root, file)
                dst_file = os.path.join(target_dir, file)
                shutil.copy2(src_file, dst_file)
        logger.info(f"Updated ship bars in {ship_bars_dst}")
    else:
        logger.warning(f"Ship bars source not found: {ship_bars_src}")

def clean_up(wows_path):
    """
    清理临时文件
    """
    logger.info("清理临时文件...")
    files_to_remove = ["extract.py", "wowsunpack.exe"]
    dirs_to_remove = ["res_extract"]

    for f in files_to_remove:
        path = os.path.join(wows_path, f)
        if os.path.exists(path):
            try:
                os.remove(path)
                logger.info(f"已删除 {path}")
            except Exception as e:
                logger.warning(f"删除失败 {path}: {e}")

    for d in dirs_to_remove:
        path = os.path.join(wows_path, d)
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
                logger.info(f"已删除目录 {path}")
            except Exception as e:
                logger.warning(f"删除目录失败 {path}: {e}")


def main():
    args = parse_args()
    wows_path = args.wows_path
    target_version = args.version
    version_normalized = normalize_version(target_version)

    logger.info(f"开始更新过程: 目标版本 {target_version} ({version_normalized})")
    logger.info(f"游戏路径: {wows_path}")

    check_files(wows_path)
    execute_extraction(wows_path)
    move_resources(wows_path)
    update_maps(wows_path)
    update_replay_unpack(wows_path, version_normalized)
    run_generators()
    update_renderer(version_normalized, wows_path)
    clean_up(wows_path)

    logger.info("所有更新任务已完成！")


if __name__ == "__main__":
    main()
