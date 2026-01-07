# 故障排除指南

## 问题：前端显示"无LLM支持，无法生成对话"

### 可能的原因

1. **API Key 未设置**
   - 后端启动时没有正确加载环境变量
   - 环境变量名称错误

2. **后端未正确初始化客户端**
   - 启动时 API Key 检查失败

### 解决方案

#### 方法1：使用带环境变量的启动脚本（推荐）

```bash
start_backend_with_env.bat
```

这个脚本会自动设置 API Key 并启动后端。

#### 方法2：手动设置环境变量

**Windows PowerShell:**
```powershell
$env:SILICONFLOW_API_KEY="sk-rtuewwxhutakmceskujdiluyjakkxdmikddbvjzrubhsbvbv"
cd backend
python main.py
```

**Windows CMD:**
```cmd
set SILICONFLOW_API_KEY=sk-rtuewwxhutakmceskujdiluyjakkxdmikddbvjzrubhsbvbv
cd backend
python main.py
```

**Linux/Mac:**
```bash
export SILICONFLOW_API_KEY="sk-rtuewwxhutakmceskujdiluyjakkxdmikddbvjzrubhsbvbv"
cd backend
python main.py
```

#### 方法3：测试API连接

运行测试脚本检查API是否可用：

```bash
cd backend
python test_api.py
```

或者使用检查脚本：

```bash
cd backend
check_env.bat
```

### 验证步骤

1. **检查后端启动日志**
   - 应该看到：`✅ API Key已配置: sk-rtuewwx...`
   - 应该看到：`✅ LLM客户端初始化成功`
   - 如果看到：`⚠️  警告: 未检测到API Key`，说明环境变量未设置

2. **检查后端控制台输出**
   - 启动时应该显示API连接状态
   - 如果有错误，会显示具体错误信息

3. **测试API端点**
   - 访问 `http://localhost:8000/` 应该返回正常响应
   - 检查浏览器控制台是否有错误

### 常见错误

#### 错误1：`未找到API Key`
**原因**: 环境变量未设置或名称错误

**解决**: 
- 使用 `start_backend_with_env.bat` 启动
- 或手动设置环境变量

#### 错误2：`LLM客户端初始化失败`
**原因**: API Key 格式错误或网络问题

**解决**:
- 检查 API Key 是否正确
- 检查网络连接
- 运行 `python test_api.py` 测试连接

#### 错误3：`LLM服务不可用：未配置API Key`
**原因**: 后端启动时没有加载环境变量

**解决**:
- 重启后端服务器
- 确保使用正确的启动方式（带环境变量）

### 调试技巧

1. **查看后端日志**
   - 启动时会显示详细的初始化信息
   - 注意查看是否有警告或错误

2. **使用测试脚本**
   ```bash
   cd backend
   python test_api.py
   ```

3. **检查环境变量**
   ```bash
   # Windows CMD
   echo %SILICONFLOW_API_KEY%
   
   # Windows PowerShell
   echo $env:SILICONFLOW_API_KEY
   
   # Linux/Mac
   echo $SILICONFLOW_API_KEY
   ```

4. **检查后端API状态**
   - 访问 `http://localhost:8000/`
   - 应该返回 `{"message": "多智能体故事世界API", "status": "running"}`

### 如果问题仍然存在

1. 确认后端服务器正在运行（端口8000）
2. 确认前端正确连接到后端（检查浏览器控制台）
3. 检查后端控制台的错误信息
4. 运行 `python test_api.py` 确认API连接正常

