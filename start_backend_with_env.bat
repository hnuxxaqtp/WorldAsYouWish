@echo off
echo ========================================
echo 启动后端服务器（带环境变量）
echo ========================================
echo.
echo 设置API Key环境变量...
set SILICONFLOW_API_KEY=sk-rtuewwxhutakmceskujdiluyjakkxdmikddbvjzrubhsbvbv
set OPENAI_API_KEY=sk-rtuewwxhutakmceskujdiluyjakkxdmikddbvjzrubhsbvbv
echo ✅ 环境变量已设置
echo.
echo 启动后端服务器...
cd backend
python main.py
pause

