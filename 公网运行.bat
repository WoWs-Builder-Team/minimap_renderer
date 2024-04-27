chcp 65001

cd src

activate yuyuko_minimap_renderer && uvicorn render_web:app --host "0.0.0.0" --port 8000

pause
