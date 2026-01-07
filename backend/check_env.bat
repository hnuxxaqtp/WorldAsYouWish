@echo off
echo 检查环境变量配置...
echo.
echo SILICONFLOW_API_KEY: %SILICONFLOW_API_KEY%
echo OPENAI_API_KEY: %OPENAI_API_KEY%
echo.
if "%SILICONFLOW_API_KEY%"=="" (
    if "%OPENAI_API_KEY%"=="" (
        echo ❌ 未设置API Key环境变量！
        echo.
        echo 请运行以下命令设置：
        echo set SILICONFLOW_API_KEY=sk-rtuewwxhutakmceskujdiluyjakkxdmikddbvjzrubhsbvbv
        echo.
    ) else (
        echo ✅ 找到 OPENAI_API_KEY
    )
) else (
    echo ✅ 找到 SILICONFLOW_API_KEY
)
echo.
echo 测试API连接...
python test_api.py
pause

