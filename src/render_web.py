import io
import json
import os
import secrets
import uuid
from typing import Annotated

from fastapi import FastAPI, UploadFile, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from renderer.render import Renderer
from replay_parser import ReplayParser

app = FastAPI()
security = HTTPBasic()


def get_current_username(
        credentials: Annotated[HTTPBasicCredentials, Depends(security)],
):
    with open(os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + "/token.json", 'r', encoding='utf8') as json_f:
        json_data = json.load(json_f)

    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = str(json_data['username']).encode("utf8")
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )
    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = str(json_data['password']).encode("utf8")
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.post("/uploadRep")
async def upload_rep(file: UploadFile, username: Annotated[str, Depends(get_current_username)]):
    video_name = str(uuid.uuid1()) + '.mp4'
    uuid_str_mp4 = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + '/temp/' + video_name
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
