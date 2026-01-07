# 多智能体故事世界系统

从小说数据生成可交互的多智能体故事世界，角色、地点、地图等均由预设/提取的资料驱动，LLM 负责角色计划、对话、世界推进和事件生成。

## 🌟 系统特性

- **前后端分离架构**: FastAPI 后端 + React 前端
- **多智能体系统**: 每个角色是一个独立的智能体，可以制定计划、进行对话、执行行动
- **数据驱动**: 角色、地点、地图等均由预设/提取的资料驱动
- **LLM 驱动**: 使用 SiliconFlow 的 Qwen/Qwen2.5-7B-Instruct 免费模型负责角色计划、对话、世界推进和事件生成
- **实时交互**: 支持实时查看角色状态、生成对话、推进世界时间、生成事件

## 🏗️ 系统架构

```
backend/                    # 后端API服务器
├── main.py                # FastAPI主应用
├── agent_system.py        # 多智能体系统
├── world_engine.py        # 世界引擎（事件生成、时间推进）
├── data_loader.py         # 数据加载器
└── requirements.txt       # Python依赖

frontend/                  # 前端界面
├── src/
│   ├── App.jsx           # 主应用组件
│   ├── components/       # UI组件
│   │   ├── CharacterPanel.jsx    # 角色面板
│   │   ├── WorldMap.jsx          # 世界地图
│   │   ├── DialogueSystem.jsx   # 对话系统
│   │   ├── EventTimeline.jsx    # 事件时间线
│   │   └── WorldControl.jsx     # 世界控制
│   └── ...
├── package.json          # Node.js依赖
└── vite.config.js        # Vite配置

graphs/                   # 角色数据（从原系统）
world_graph/              # 世界状态数据
tkg/                      # 时间知识图谱
```

## 🚀 快速开始

### 1. 环境准备

#### 后端环境

```bash
cd backend
pip install -r requirements.txt
```

#### 前端环境

```bash
cd frontend
npm install
```

### 2. API密钥配置

系统使用 SiliconFlow 的 Qwen/Qwen2.5-7B-Instruct 免费模型。

**API Key 已内置在配置文件中**（`backend/config.py`），无需设置环境变量，直接启动即可使用。

如果需要修改 API Key，可以编辑 `backend/config.py` 文件中的 `DEFAULT_API_KEY` 变量。

**可选**: 如果设置了环境变量 `SILICONFLOW_API_KEY` 或 `OPENAI_API_KEY`，系统会优先使用环境变量的值。

### 3. 启动系统

#### 启动后端（终端1）

```bash
cd backend
python main.py
```

后端将在 `http://localhost:8000` 启动

#### 启动前端（终端2）

```bash
cd frontend
npm run dev
```

前端将在 `http://localhost:3000` 启动

### 4. 使用系统

1. 打开浏览器访问 `http://localhost:3000`
2. 点击"初始化世界"按钮
3. 系统将从 `graphs/canon/` 和 `world_graph/canon/` 加载数据
4. 开始交互：
   - 查看角色列表和详情
   - 为角色生成计划
   - 生成角色间对话
   - 推进世界时间
   - 在特定地点生成事件

## 📡 API接口

### 世界管理

- `POST /api/world/init` - 初始化世界
- `GET /api/world/state` - 获取当前世界状态

### 角色管理

- `GET /api/characters` - 获取所有角色
- `GET /api/characters/{name}` - 获取特定角色信息
- `POST /api/characters/{name}/plan` - 为角色生成计划

### 对话系统

- `POST /api/dialogue` - 生成角色对话

### 世界推进

- `POST /api/world/advance` - 推进世界时间
- `POST /api/events/generate` - 生成事件

### 数据查询

- `GET /api/locations` - 获取所有地点
- `GET /api/relations` - 获取角色关系图
- `GET /api/timeline` - 获取事件时间线

## 🎮 功能说明

### 角色智能体

每个角色都是一个独立的智能体，具有：

- **属性**: 战斗力、性格特质、物品清单
- **状态**: 位置、状态、目标
- **关系**: 与其他角色的关系网络
- **能力**: 
  - 制定计划（基于角色设定和世界状态）
  - 生成对话（考虑角色性格和关系）
  - 执行行动（符合角色设定）

### 世界引擎

负责：

- **时间推进**: 推进世界时间，自动生成事件
- **事件生成**: 基于世界状态和角色情况生成合理事件
- **地点管理**: 管理世界中的地点和角色位置

### 对话系统

- 选择说话者和倾听者
- 可选话题
- LLM生成符合角色性格和关系的对话

### 事件时间线

- 显示所有发生的事件
- 按时间排序
- 显示事件详情（地点、参与者、重要性等）

## 🔧 数据格式

系统从以下数据源加载：

1. **角色数据**: `graphs/{worldline_id}/chapter_001.characters.json`
2. **关系数据**: `graphs/{worldline_id}/chapter_001.relations.json`
3. **世界状态**: `world_graph/{worldline_id}/chapter_001.json`

数据格式与原系统保持一致。

## 🛠️ 开发

### 后端开发

```bash
cd backend
# 安装依赖
pip install -r requirements.txt

# 运行开发服务器（自动重载）
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 前端开发

```bash
cd frontend
# 安装依赖
npm install

# 运行开发服务器
npm run dev
```

## 📝 注意事项

1. **API密钥**: API Key 已内置在 `backend/config.py` 中，无需额外配置即可使用
2. **模型**: 系统使用 SiliconFlow 的 Qwen/Qwen2.5-7B-Instruct 免费模型，API 兼容 OpenAI 格式
3. **环境变量**: 如果设置了环境变量 `SILICONFLOW_API_KEY` 或 `OPENAI_API_KEY`，会优先使用环境变量的值
2. **数据文件**: 确保 `graphs/` 和 `world_graph/` 目录下有数据文件
3. **端口冲突**: 如果端口被占用，可以修改配置文件中的端口号

## 🔮 未来扩展

- [ ] 角色自动行动系统
- [ ] 更复杂的地图可视化
- [ ] 角色记忆系统
- [ ] 多章节支持
- [ ] 实时协作功能
- [ ] 故事导出功能

## 📄 许可证

MIT License

