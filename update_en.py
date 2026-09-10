import argparse
import os
import shutil
import subprocess
import logging
import sys
import glob
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_args():
    """
    Parse command line arguments
    """
    parser = argparse.ArgumentParser(
        description="Automate update of World of Warships resources and code"
    )
    parser.add_argument(
        "--wows-path",
        required=True,
        help="World of Warships game installation root directory path",
    )
    parser.add_argument(
        "--version", required=True, help="Target update version number (e.g., 14.8.0)"
    )
    return parser.parse_args()


def normalize_version(version):
    """
    Convert version number to underscore format (e.g., 14.8.0 -> 14_8_0)
    """
    return version.replace(".", "_")


def check_files(wows_path):
    """
    Check if necessary files exist
    """
    required_files = ["extract.py", "wowsunpack.exe"]
    for f in required_files:
        if not os.path.exists(f):
            logger.error(f"Missing necessary file: {f}")
            sys.exit(1)

    if not os.path.exists(wows_path):
        logger.error(f"Game path does not exist: {wows_path}")
        sys.exit(1)

    logger.info("Necessary files check passed.")


def execute_extraction(wows_path):
    """
    Execute resource extraction
    """
    logger.info("Starting resource extraction...")

    # Copy tools to game directory
    try:
        shutil.copy("extract.py", wows_path)
        shutil.copy("wowsunpack.exe", wows_path)
        logger.info(f"Copied extract.py and wowsunpack.exe to {wows_path}")
    except Exception as e:
        logger.error(f"Failed to copy tools: {e}")
        sys.exit(1)

    # Execute extraction script
    # extract.py extracts the latest bin version by default
    cmd = [sys.executable, "extract.py"]
    try:
        subprocess.run(cmd, cwd=wows_path, check=True)
        logger.info("Resource extraction completed.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Extraction script execution failed: {e}")
        sys.exit(1)


def move_resources(wows_path):
    """
    Move extracted key resources to project resources directory
    """
    logger.info("Moving key resources...")
    extract_root = os.path.join(wows_path, "res_extract")
    target_res_dir = "resources"

    if not os.path.exists(extract_root):
        logger.error(f"Extraction directory does not exist: {extract_root}")
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
            logger.info(f"Copied {count} {name} to {dst}")
        else:
            logger.warning(f"{name} resource dir not found: {src}")

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

    # 1. Move GameParams.data
    gp_src = os.path.join(extract_root, "content", "GameParams.data")
    if os.path.exists(gp_src):
        shutil.copy(gp_src, os.path.join(target_res_dir, "GameParams.data"))
        logger.info(f"GameParams.data updated")
    else:
        logger.warning(f"GameParams.data not found: {gp_src}")

    # 2. Move global.mo (Only search for English)
    # Path structure is usually: texts/{locale}/LC_MESSAGES/global.mo
    texts_dir = os.path.join(extract_root, "texts")
    mo_src = None

    # Priority: en
    locales_to_try = ["en"]

    if os.path.exists(texts_dir):
        # Attempt to find specific language
        for locale in locales_to_try:
            candidate = os.path.join(texts_dir, locale, "LC_MESSAGES", "global.mo")
            if os.path.exists(candidate):
                mo_src = candidate
                logger.info(f"Found language file ({locale}): {mo_src}")
                break

        # If priority language not found, try to find any existing global.mo
        if not mo_src:
            candidates = glob.glob(
                os.path.join(texts_dir, "*", "LC_MESSAGES", "global.mo")
            )
            if candidates:
                mo_src = candidates[0]
                logger.info(f"Found alternative language file: {mo_src}")

    if mo_src and os.path.exists(mo_src):
        shutil.copy(mo_src, os.path.join(target_res_dir, "global.mo"))
        logger.info(f"global.mo updated")
    else:
        logger.warning(f"global.mo not found in {texts_dir}")


def update_maps(wows_path):
    """
    Update maps/spaces
    """
    logger.info("Updating maps/spaces...")
    extract_spaces = os.path.join(wows_path, "res_extract", "spaces")
    target_spaces = os.path.join("maps", "spaces")

    if not os.path.exists(extract_spaces):
        logger.warning(f"Extracted spaces directory not found: {extract_spaces}")
        return

    # Use copytree to merge/overwrite
    # Note: extract.py extracted minimap*.png and space.settings
    # We copy these files to maps/spaces, preserving original structure

    for root, dirs, files in os.walk(extract_spaces):
        rel_path = os.path.relpath(root, extract_spaces)
        target_dir = os.path.join(target_spaces, rel_path)

        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        for file in files:
            src_file = os.path.join(root, file)
            dst_file = os.path.join(target_dir, file)
            shutil.copy2(src_file, dst_file)

    logger.info("maps/spaces update completed.")


def update_replay_unpack(wows_path, version_normalized):
    """
    Update src/replay_unpack
    1. Create new version directory
    2. Copy Python scripts from previous version
    3. Copy newly extracted scripts (XML/DEF)
    """
    logger.info(f"Updating src/replay_unpack (version: {version_normalized})...")

    base_path = os.path.join("src", "replay_unpack", "clients", "wows", "versions")
    new_version_path = os.path.join(base_path, version_normalized)

    # Find previous version
    versions = []
    if os.path.exists(base_path):
        for d in os.listdir(base_path):
            if os.path.isdir(os.path.join(base_path, d)) and d[0].isdigit():
                versions.append(d)

    versions.sort(key=lambda s: list(map(int, s.split("_"))))

    if not versions:
        logger.error("No existing version found, cannot base copy.")
        return

    last_version = versions[-1]
    logger.info(f"Detected previous version: {last_version}")

    if os.path.exists(new_version_path):
        logger.warning(
            f"Target version directory already exists: {new_version_path}, will overwrite/merge."
        )
    else:
        os.makedirs(new_version_path)

    # Copy Python files (.py) from previous version
    last_version_path = os.path.join(base_path, last_version)
    for file in os.listdir(last_version_path):
        if file.endswith(".py"):
            src_file = os.path.join(last_version_path, file)
            dst_file = os.path.join(new_version_path, file)
            shutil.copy2(src_file, dst_file)

    # Copy extracted scripts
    extract_scripts = os.path.join(wows_path, "res_extract", "scripts")
    target_scripts = os.path.join(new_version_path, "scripts")

    if os.path.exists(extract_scripts):
        if os.path.exists(target_scripts):
            shutil.rmtree(target_scripts)
        shutil.copytree(extract_scripts, target_scripts)
        logger.info(f"Copied scripts to {target_scripts}")
    else:
        logger.warning(f"Extracted scripts directory not found: {extract_scripts}")


def run_generators():
    """
    Run generation scripts: create_data.py and maps/spaces.py
    """
    logger.info("Running generation scripts...")

    # Run create_data.py
    try:
        logger.info("Executing create_data.py ...")
        subprocess.run([sys.executable, "create_data.py"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"create_data.py execution failed: {e}")
        sys.exit(1)

    # Run maps/spaces.py
    try:
        logger.info("Executing maps/spaces.py ...")
        # maps/spaces.py is run as a script
        subprocess.run([sys.executable, os.path.join("maps", "spaces.py")], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"maps/spaces.py execution failed: {e}")
        sys.exit(1)


def update_renderer(version_normalized):
    """
    Update src/renderer
    1. Create new version resource directory
    2. Copy generated json data
    3. Update global spaces
    """
    logger.info(f"Updating src/renderer (version: {version_normalized})...")

    # 1. Create new version resource directory
    renderer_ver_path = os.path.join(
        "src", "renderer", "versions", version_normalized, "resources"
    )
    os.makedirs(renderer_ver_path, exist_ok=True)

    # Create __init__.py to make it a package
    Path(
        os.path.join("src", "renderer", "versions", version_normalized, "__init__.py")
    ).touch()
    Path(os.path.join(renderer_ver_path, "__init__.py")).touch()

    # 2. Apply generated data (generated/ -> renderer_ver/resources/)
    generated_dir = "generated"
    json_files = glob.glob(os.path.join(generated_dir, "*.json"))

    if not json_files:
        logger.warning("No JSON files found in generated/ directory.")

    for json_file in json_files:
        shutil.copy(json_file, renderer_ver_path)
        logger.info(f"Copied {os.path.basename(json_file)}")

    # 3. Update global src/renderer/resources/spaces
    # Source: maps/spaces (processed by maps/spaces.py)
    maps_spaces_dir = os.path.join("maps", "spaces")
    renderer_spaces_dir = os.path.join("src", "renderer", "resources", "spaces")

    logger.info("Syncing maps/spaces to src/renderer/resources/spaces ...")

    if os.path.exists(renderer_spaces_dir):
        shutil.rmtree(renderer_spaces_dir)

    shutil.copytree(maps_spaces_dir, renderer_spaces_dir)
    logger.info("Global spaces update completed.")


def clean_up(wows_path):
    """
    Clean up temporary files
    """
    logger.info("Clean up temporary files...")
    files_to_remove = ["extract.py", "wowsunpack.exe"]
    dirs_to_remove = ["res_extract"]

    for f in files_to_remove:
        path = os.path.join(wows_path, f)
        if os.path.exists(path):
            try:
                os.remove(path)
                logger.info(f"Deleted {path}")
            except Exception as e:
                logger.warning(f"Failed to delete {path}: {e}")

    for d in dirs_to_remove:
        path = os.path.join(wows_path, d)
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
                logger.info(f"Deleted directory {path}")
            except Exception as e:
                logger.warning(f"Failed to delete directory {path}: {e}")


def main():
    args = parse_args()
    wows_path = args.wows_path
    target_version = args.version
    version_normalized = normalize_version(target_version)

    logger.info(
        f"Starting update process: Target version {target_version} ({version_normalized})"
    )
    logger.info(f"Game path: {wows_path}")

    check_files(wows_path)
    execute_extraction(wows_path)
    move_resources(wows_path)
    update_maps(wows_path)
    update_replay_unpack(wows_path, version_normalized)
    run_generators()
    update_renderer(version_normalized)
    clean_up(wows_path)

    logger.info("All update tasks completed!")


if __name__ == "__main__":
    main()
