conda create --name yuyuko_minimap_renderer python=3.10
activate yuyuko_minimap_renderer
pip install -r requirements-yuyuko.txt -i  http://mirrors.aliyun.com/pypi/simple --trusted-host mirrors.aliyun.com
pip install "uvicorn[standard]" -i  http://mirrors.aliyun.com/pypi/simple --trusted-host mirrors.aliyun.com
pause
