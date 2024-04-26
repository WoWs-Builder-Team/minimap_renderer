import io
import os
import uuid

from fastapi import FastAPI, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse

from renderer.render import Renderer
from replay_parser import ReplayParser

app = FastAPI()


@app.post("/uploadRep")
async def upload_rep(file: UploadFile):
    uuid_str_mp4 = os.path.dirname(os.path.abspath(__file__)) + '/temp/' + str(uuid.uuid1()) + '.mp4'
    binary_stream = io.BytesIO(file.file.read())
    replay_info = ReplayParser(
        binary_stream, strict=True, raw_data_output=False
    ).get_info()
    renderer = Renderer(
        replay_info["hidden"]["replay_data"],
        logs=True,
        enable_chat=True,
        use_tqdm=True,
    )
    renderer.start(str(uuid_str_mp4))
    # 清理文件
    task = BackgroundTasks()
    task.add_task(del_file, uuid_str_mp4)
    return FileResponse(uuid_str_mp4, media_type="video/mp4", background=task)


def del_file(file_name):
    os.remove(file_name)
