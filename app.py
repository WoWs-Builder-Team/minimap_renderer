import subprocess
import sys
import os
import importlib.util

from pathlib import Path
import webbrowser
import time

python = sys.executable


def run(command, desc=None, errdesc=None, custom_env=None):
    if desc is not None:
        print(desc)

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, env=os.environ if custom_env is None else custom_env)

    if result.returncode != 0:

        message = f"""{errdesc or 'Error running command'}.
Command: {command}
Error code: {result.returncode}
stdout: {result.stdout.decode(encoding="utf8", errors="ignore") if len(result.stdout)>0 else '<empty>'}
stderr: {result.stderr.decode(encoding="utf8", errors="ignore") if len(result.stderr)>0 else '<empty>'}
"""
        raise RuntimeError(message)

    return result.stdout.decode(encoding="utf8", errors="ignore")

def is_installed(package):
    try:
        spec = importlib.util.find_spec(package)
    except ModuleNotFoundError:
        return False

    return spec is not None

def run_pip_from_git(url=None, desc=None, args=""):
    return run(f'"{python}" -m pip install git+{url} {args}', desc=f"Installing {desc}", errdesc=f"Couldn't install {desc}")

def run_pip(pkg, desc=None, args=""):
    return run(f'"{python}" -m pip install {pkg} {args}', desc=f"Installing {desc}", errdesc=f"Couldn't install {desc}")

def main(page):
    # rendering
    def on_dialog_result(e: ft.FilePickerResultEvent):
        if not e.files:
            return
        else:
            files = [file.path for file in e.files]
            body.controls.pop(0)
            body.update()
            progs = []
            for file in files:
                path = Path(file)
                prog = ft.Column([ft.Text(f"{path.stem}.mp4", style=ft.TextThemeStyle.BODY_LARGE)])
                body.controls.append(prog)
                progs.append(prog)

                body.update()
            for index, file in enumerate(files):
                try:
                    progs[index].controls.append(ft.ProgressBar())
                    body.update()

                    path = Path(file)
                    video_path = output_path.joinpath(f"{path.stem}.mp4")
                    with open(path, "rb") as f:
                        LOGGER.info("Parsing the replay file...")
                        replay_info = ReplayParser(
                            f, strict=True, raw_data_output=False
                        ).get_info()
                        LOGGER.info("Rendering the replay file...")
                        renderer = Renderer(
                            replay_info["hidden"]["replay_data"],
                            logs=True,
                            use_tqdm=True,
                            enable_chat=setting_chat.value,
                            anon= setting_anon.value,
                        )
                        renderer.start(str(video_path))
                        LOGGER.info(f"The video file is at: {str(video_path)}")

                        progs[index].controls.pop(1)
                        progs[index].controls[0] = ft.Text(f"✅ {path.stem}.mp4 ", style=ft.TextThemeStyle.BODY_LARGE)


                except:
                    progs[index].controls.pop(1)
                    body.controls[index] = ft.Text(f"❌ {path.stem}.mp4", style=ft.TextThemeStyle.BODY_LARGE)
                
                body.update()
                    
            body.controls = [upload_container]
            time.sleep(2)
            body.update()

            os.startfile(output_path)

    def set_output_folder(e: ft.FilePickerResultEvent):
        if not e.path:
            return
        else:
            page.client_storage.set("output_path", str(e.path))
            output_path_title.value = f"{str(e.path)}\\"
            output_path_title.update()

    def update_renderer(e):
        print('update')
        print(e)
        body.controls = [ft.Column([
            ft.Text("Updating modules, it might take a few minutes... ", style=ft.TextThemeStyle.BODY_LARGE),
            ft.ProgressBar(),
        ])]
        body.update()
        run_pip_from_git("https://github.com/WoWs-Builder-Team/minimap_renderer.git", "minimap_renderer", "-U")
        body.controls = [upload_container]
        page.snack_bar = ft.SnackBar(ft.Text("Updated succesfully!"),
            action = "Alright!",
            bgcolor = "green"
        )
        page.snack_bar.open = True
        page.update()

    # reading settings
    if page.client_storage.contains_key("output_path"):
        output_path = Path(page.client_storage.get("output_path"))
        
    else:
        output_path = Path(os.getcwd()).joinpath("output_videos")
        output_path.mkdir(parents=True, exist_ok=True)

    # components
    github_btn = ft.ElevatedButton(
        "Github", 
        icon=ft.icons.HOME_ROUNDED,
        on_click=lambda _: webbrowser.open('https://github.com/WoWs-Builder-Team/minimap_renderer', new=0),
        style=ft.ButtonStyle(
            # color = {
            #     ft.MaterialState.HOVERED: "green",
            #     ft.MaterialState.DEFAULT: "blue",
            # },
            shape = buttons.RoundedRectangleBorder(radius=2), 
        )
    )

    body = ft.ResponsiveRow([],
        vertical_alignment= ft.CrossAxisAlignment.CENTER,
        height=600,
    )

    upload_container = ft.Container(
        ft.Text("Select replays", style=ft.TextThemeStyle.DISPLAY_MEDIUM),
        alignment = ft.alignment.center,
        border = ft.border.all(5, "#C0C0C0"),
        on_click=lambda _: file_picker.pick_files(allowed_extensions=["wowsreplay"], allow_multiple=True)
    )
    
    body.controls.append(upload_container)

    # menu
    setting_chat = ft.Checkbox(label="Enable chat", value=True, fill_color="#C0C0C0", tooltip="render chat history or not")
    setting_anon = ft.Checkbox(label="anonymous mode", value=False, fill_color="#C0C0C0", tooltip="players' ign will be replaced by tags")
    setting = ft.PopupMenuButton(
        icon = ft.icons.SETTINGS,
        items = [
            ft.PopupMenuItem(text="render setting", content=ft.Column([
                ft.Text("Render setting", style=ft.TextThemeStyle.BODY_LARGE),
                setting_chat,
                setting_anon,
            ])),
            ft.PopupMenuItem(), # divider

            # ft.PopupMenuItem(text="D:\Codes\minimap_renderer\Codes\minimap_renderer", on_click = lambda _: output_folder_picker.get_directory_path()), # divider
            ft.PopupMenuItem(text="output setting", content=ft.Column([
                ft.Text("Output setting", tooltip="current output folder", style=ft.TextThemeStyle.BODY_LARGE),
                output_path_title := ft.Text(f"{output_path}\\", style=ft.TextThemeStyle.BODY_SMALL),
                ft.ElevatedButton(
                    "change folder",
                    tooltip = "change output folder",
                    on_click =lambda _: output_folder_picker.get_directory_path(),
                    style=ft.ButtonStyle(
                        shape=buttons.RoundedRectangleBorder(radius=2),
                    )
                ),
            ])),
            ft.PopupMenuItem(), # divider
            ft.PopupMenuItem(content=ft.Column([
                ft.Text("Update", style=ft.TextThemeStyle.BODY_LARGE),
                ft.ElevatedButton(
                    "update modules",
                    tooltip = "click it if WOWS updated recently and this tool failed to run",
                    on_click = update_renderer,
                    style=ft.ButtonStyle(
                        shape=buttons.RoundedRectangleBorder(radius=2),
                    )
                )
        ])),
            ft.PopupMenuItem(), # divider
            ft.PopupMenuItem(
                content = ft.Text("GUI made by B2U#0900", style=ft.TextThemeStyle.BODY_SMALL),
            ),
            
        ]
    )

    # app bar
    page.appbar = ft.AppBar(
        leading=ft.Icon(ft.icons.MAP),
        leading_width=40,
        title=ft.Text("Minimap renderer V1.0"),
        center_title=False,
        bgcolor=ft.colors.SURFACE_VARIANT,
        actions=[
            github_btn,
            setting
        ],
    )
    
    # filer pickers
    file_picker = ft.FilePicker(on_result=on_dialog_result)
    output_folder_picker = ft.FilePicker(on_result=set_output_folder)
    page.overlay.append(file_picker)
    page.overlay.append(output_folder_picker)

    # page
    page.add(
        body
    )
    page.update()

if __name__ == "__main__":

    if not is_installed("renderer"):
        print("this might take a few minutes...")
        run_pip_from_git("https://github.com/WoWs-Builder-Team/minimap_renderer.git", "minimap_renderer", "-U")
        
        
    if not is_installed("flet"):
        run_pip("flet", "flet")

    from renderer.render import Renderer # type: ignore
    from replay_parser import ReplayParser # type: ignore
    from renderer.utils import LOGGER # type: ignore

    import flet as ft
    from flet import buttons

    ft.app(target=main)


