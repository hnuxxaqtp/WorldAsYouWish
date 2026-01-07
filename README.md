<<<<<<< HEAD
# WorldAsYouWish
=======
# 叙事代理系统 - 智能故事创作与分支管理平台

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-16+-green.svg)](https://nodejs.org/)
[![React](https://img.shields.io/badge/React-18.2+-61dafb.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 项目名称

**项目名称**: 叙事代理系统 - Multi-Agent Narrative System
**项目类型**: 智能故事创作平台 / 多智能体仿真系统

## 运行环境

### 后端环境
- **Python**: Python 3.8 或更高版本
- **操作系统**: Windows 10/11, macOS, Linux
- **内存建议**: 至少 8GB RAM
- **存储空间**: 至少 2GB 可用空间（用于模型和数据存储）

### 前端环境
- **Node.js**: Node.js 16.0 或更高版本
- **npm**: npm 7.0 或更高版本
- **浏览器**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+

### AI 模型要求
- **LLM API**: 需要 SiliconFlow API Key（Qwen2.5-7B-Instruct）或 OpenAI API Key
- **向量模型**: 自动下载 `paraphrase-multilingual-MiniLM-L12-v2` 模型（约 400MB）

## 🌟 项目概述

**叙事代理系统**是一个基于大语言模型的智能故事创作平台，实现了完整的**章节级修改机制**、**时间知识图谱(TKG)抽取**、**人物关系图管理**和**世界线分支系统**。系统能够将自然语言故事转换为结构化数据，支持用户进行智能化的故事编辑和分支创作。

### 🎯 核心特性

- **🤖 智能章节重写**: 基于用户修改自动重写后续剧情，保持故事连贯性
- **📊 结构化数据抽取**: 自动生成TKG四元组、人物属性表、关系图
- **🌳 世界线分支管理**: 支持canon和user_branch双分支，保护原始数据
- **🎭 人物数据驱动**: LLM参考角色画像和关系图进行剧情推理
- **🔄 增量式更新**: 基于上一章快照进行增量更新，保证数据一致性
- **⚡ 实时交互**: 支持chunk级播放和章节级编辑的混合交互模式

## 🏗️ 系统架构

### 核心模块

```
narrative_agent.py          # 主程序 - 交互式故事创作引擎
├── 章节级修改机制
├── 世界线分支管理
├── 人物数据集成
└── 交互式命令系统

state_extractor.py          # 数据抽取器 - LLM结构化抽取
├── 章节状态抽取
├── TKG四元组抽取
├── 人物图抽取
└── 重试与校验机制

tkg_models.py              # 数据模型 - Pydantic强类型定义
├── TKGEntry (四元组)
├── CharacterAttributes (角色属性)
├── RelationsSnapshot (关系图)
└── EventFeasibility (事件可行性)

build_chapter_states.py    # 构建脚本 - 首次运行数据生成
└── 完整数据流水线构建
```

### 数据流架构

```
输入文本 → 章节分割 → LLM抽取 → 结构化数据 → 分支存储
    ↓           ↓         ↓         ↓         ↓
  Chapter1-3.txt → Chunks → Events/Relations → JSON/JSONL → canon/user_branch
```

## 📁 目录结构

```
World_developer/
├── 📄 核心文件
│   ├── narrative_agent.py          # 主程序
│   ├── state_extractor.py          # 数据抽取器
│   ├── tkg_models.py              # 数据模型
│   ├── narrative_state.py         # 状态定义
│   ├── build_chapter_states.py    # 构建脚本
│   └── requirements.txt           # 依赖管理
│
├── 📊 数据目录
│   ├── world_graph/               # 章节状态快照
│   │   ├── canon/                # 原始世界线
│   │   │   ├── chapter_001.json  # 章节状态
│   │   │   └── index.json        # 索引文件
│   │   └── user_branch/          # 用户修改分支
│   │       └── chapter_001.json  # 修改后状态
│   │
│   ├── tkg/                      # 时间知识图谱
│   │   ├── canon/                # 原始TKG
│   │   │   └── chapter_001.tkg.jsonl  # 四元组流
│   │   └── user_branch/          # 修改后TKG
│   │
│   └── graphs/                   # 人物图数据
│       ├── canon/                # 原始人物图
│       │   ├── chapter_001.characters.json  # 角色属性
│       │   └── chapter_001.relations.json   # 关系图
│       └── user_branch/          # 修改后人物图
│
├── ⚙️ 配置文件
│   ├── trait_vocab.json          # 性格特质词汇表
│   ├── relation_vocab.json       # 关系类型词汇表
│   ├── graph_update_rules.yaml   # 图更新规则
│   └── aliases.yaml              # 实体别名映射
│
└── 📖 示例文件
    └── Chapter1-3.txt            # 示例故事文本
```

## 📦 依赖库及安装命令

### 后端依赖（Python）

#### 核心依赖
```bash
pip install -r requirements.txt
```

核心依赖包括：
- `openai>=1.0.0` - OpenAI API 客户端（兼容 SiliconFlow API）
- `pydantic>=2.0.0` - 数据验证模型

#### 后端完整依赖
```bash
cd backend
pip install -r requirements.txt
```

后端完整依赖包括：
- `fastapi>=0.104.0` - Web 框架
- `uvicorn[standard]>=0.24.0` - ASGI 服务器
- `sentence-transformers==2.7.0` - 向量嵌入模型
- `torch>=2.0.0,<2.2.0` - PyTorch 深度学习框架
- `transformers>=4.30.0,<4.40.0` - HuggingFace Transformers
- `numpy>=1.24.0,<2.0.0` - 数值计算
- `scipy>=1.9.0` - 科学计算
- `scikit-learn>=1.0.0` - 机器学习工具

### 前端依赖（Node.js）

```bash
解压frontend.zip至根目录
cd frontend
npm install
```

前端依赖包括：
- `react@^18.2.0` - React 框架
- `react-dom@^18.2.0` - React DOM
- `axios@^1.6.0` - HTTP 客户端
- `react-router-dom@^6.20.0` - 路由管理
- `recharts@^2.10.0` - 数据可视化

## 🚀 详细运行步骤

### Step 1: 环境检查

#### 1.1 检查 Python 版本
```bash
python --version
# 或
python3 --version
```
确保输出为 Python 3.8 或更高版本。

#### 1.2 检查 Node.js 版本
```bash
node --version
```
确保输出为 v16.0.0 或更高版本。

#### 1.3 检查 npm 版本
```bash
npm --version
```
确保输出为 7.0.0 或更高版本。

### Step 2: 安装 Python 依赖

#### 2.1 安装核心依赖
在项目根目录下执行：
```bash
pip install -r requirements.txt
```

#### 2.2 安装后端依赖
进入 backend 目录执行：
```bash
cd backend
pip install -r requirements.txt
cd ..
```

### Step 3: 安装前端依赖

进入 frontend 目录并安装依赖：
```bash
cd frontend
npm install
cd ..
```

### Step 4: 配置 API 密钥

本项目提供了**三种**配置 API 密钥的方式，按优先级从高到低选择：

#### 方式一：环境变量配置（推荐）

如果不希望密钥写入代码，使用环境变量配置。

**获取 API 密钥：**
- **SiliconFlow**（推荐）：访问 https://siliconflow.cn/ 注册并获取 API Key
- **OpenAI**：访问 https://platform.openai.com/ 注册并获取 API Key

**Windows CMD：**
```cmd
set SILICONFLOW_API_KEY=your-api-key-here
```

**Windows PowerShell：**
```powershell
$env:SILICONFLOW_API_KEY = "your-api-key-here"
```

**Linux/macOS：**
```bash
export SILICONFLOW_API_KEY="your-api-key-here"
```

#### 方式二：直接修改代码（简单快捷）

⚠️ **注意**：将密钥写入代码时请注意保密，不要上传到公开仓库。

**操作步骤：**

1. 打开文件 `backend/config.py`

2. 找到第 16 行的 `DEFAULT_API_KEY`：
```python
# API密钥（直接写死，避免每次设置环境变量）
DEFAULT_API_KEY = "sk-put-your-api-key-here"
```

3. 将引号中的内容替换为您的 API 密钥：
```python
DEFAULT_API_KEY = "sk-your-actual-api-key-here"
```

4. 保存文件后重新启动后端服务即可。

**代码优先级说明：**
系统会按以下顺序依次查找 API 密钥：
1. 环境变量 `SILICONFLOW_API_KEY`
2. 环境变量 `OPENAI_API_KEY`
3. 代码中的 `DEFAULT_API_KEY`（如果在 config.py 中修改了）

#### 方式三：修改配置文件（临时方案）

也可以直接在 `backend/main.py` 中临时设置，不推荐长期使用。

找到 `main.py` 中调用 `get_openai_client()` 函数的位置，传入您的密钥参数。

### Step 5: 下载向量嵌入模型

#### 5.1 自动下载（首次运行时）
首次运行后端时会自动下载模型（约 400MB），需要稳定的网络连接。

#### 5.2 手动下载（可选）
如果自动下载失败，可以手动运行：
```bash
python download_model.py
```

模型将保存到 `model/paraphrase-multilingual-MiniLM-L12-v2/` 目录。

### Step 6: 启动后端服务

#### 6.1 方式一：使用命令行启动
```bash
cd backend
python main.py
```

后端服务将在 `http://localhost:8000` 启动。

#### 6.2 方式二：使用批处理文件启动（Windows）
双击运行项目根目录下的 `start_backend.bat` 文件。

或者带环境变量启动：
```bash
start_backend_with_env.bat
```

#### 6.3 验证后端服务
打开浏览器访问 `http://localhost:8000/docs`，应看到 FastAPI 自动生成的 API 文档页面。

### Step 7: 启动前端服务

#### 7.1 方式一：使用命令行启动
在新的终端窗口中执行：
```bash
cd frontend
npm run dev
```

前端开发服务器将在 `http://localhost:5173` 启动。

#### 7.2 方式二：使用批处理文件启动（Windows）
双击运行项目根目录下的 `start_frontend.bat` 文件。

#### 7.3 验证前端服务
打开浏览器访问 `http://localhost:5173`，应看到多智能体故事世界系统的主界面。

### Step 8: 使用系统

#### 8.1 创建或选择世界
- 点击"创建新世界"按钮创建一个新世界
- 或从列表中选择一个已存在的世界

#### 8.2 主界面功能
- **角色面板**：查看和管理角色属性、情感、记忆
- **对话系统**：生成角色对话
- **事件时间线**：查看世界事件历史
- **世界地图**：可视化角色位置和地点
- **世界控制**：推进世界时间、生成事件

#### 8.3 使用命令行界面（可选）
```bash
# 启动交互式故事创作
python narrative_agent.py

# 可用命令
n/next          # 下一个剧情片段
p/prev          # 上一个剧情片段
ce <内容>       # 章节级编辑
state           # 保存章节状态
tkg             # 查看知识图谱
graph           # 查看人物关系
q/quit          # 退出
```

### Step 9: 停止服务

#### 9.1 停止后端服务
在后端终端按 `Ctrl + C`

#### 9.2 停止前端服务
在前端终端按 `Ctrl + C`

## 📋 快速启动指南（Windows 批处理文件）

#### 一键启动后端
```bash
start_backend.bat
```

#### 一键启动前端
```bash
start_frontend.bat
```

## 常见问题排查

### 问题 1: 端口被占用
```bash
# 检查端口占用（Windows）
netstat -ano | findstr :8000

# 终止进程
taskkill /PID <进程ID> /F
```

### 问题 2: Python 模块导入错误
```bash
# 重新安装依赖
cd backend
pip install --upgrade -r requirements.txt
```

### 问题 3: 前端 npm install 失败
```bash
# 清除缓存后重新安装
cd frontend
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### 问题 4: API 密钥未设置

**检查密钥配置：**

方式一 - 检查代码中的密钥：
```bash
# 查看 backend/config.py 中的 DEFAULT_API_KEY
type backend\config.py
```

方式二 - 检查环境变量：
```bash
# Windows CMD
set SILICONFLOW_API_KEY

# 验证
echo %SILICONFLOW_API_KEY%
```

方式三 - 简单验证：
启动后端时，如果看到 `✅ 已连接到 SiliconFlow API` 说明密钥正确。

如果看到 `⚠️ 未找到API Key`，请按上述方式二（修改代码）或方式一（设置环境变量）进行配置。

## 🎭 核心功能详解

### 1. 章节级修改机制

**设计理念**: 在保持chunk级播放体验的同时，实现章节级的智能重写。

```python
# 编辑限制：每个章节最多5次修改
# 编辑范围：仅限【昴】标记的内容
# 重写范围：从修改点之后的全部后续剧情
# 播放方式：仍然按chunk播放，用户无法一次性看到全部剧情
```

**工作流程**:
1. 用户使用 `ce` 命令编辑【昴】的内容
2. 系统自动定位当前chunk内的【昴】位置
3. LLM基于用户修改重写后续剧情
4. 重写完成后，新版本成为下一轮基线
5. 系统重新分割chunks，保持播放体验

**智能特性**:
- 🔄 **连续重写**: 每次重写都基于最新文本，避免跳跃
- 🎯 **精确定位**: 自动选择当前chunk内的【昴】进行编辑
- 🎨 **格式一致**: 严格保持【旁白】【角色】剧本格式
- 🧠 **人物驱动**: 参考角色画像和关系图进行剧情推理

### 2. 时间知识图谱(TKG)抽取

**数据结构**: 四元组流 `(tau, h, r, t, meta)`

```json
{
  "tau": "ch001_e1",           // 时间戳
  "h": "昴",                   // 头实体
  "r": "遇到",                 // 关系动词
  "t": "爱蜜莉雅",             // 尾实体
  "meta": {
    "location": "王都",        // 地点
    "polarity": 0.5,          // 情感极性
    "evidence": "原文片段"     // 证据
  }
}
```

**抽取特性**:
- 📊 **结构化存储**: JSONL格式，便于流式追加和查询
- 🔍 **质量保证**: 严格的关系词闭集、实体标准化、证据引用
- 📈 **增量更新**: 基于上一章快照进行增量更新
- 🎯 **约束检查**: 战斗力硬约束、关系证据要求

### 3. 人物图管理

**角色属性表**:
```json
{
  "昴": {
    "combat_power": "弱",      // 战斗力等级
    "inventory": ["木箱"],     // 物品清单
    "traits": ["勇敢", "灵活"]  // 性格特质
  }
}
```

**关系图**:
```json
{
  "nodes": ["昴", "爱蜜莉雅", "雷姆"],
  "edges": [
    {
      "a": "昴",
      "b": "爱蜜莉雅",
      "type": "同伴",
      "score": 0.8,
      "evidence": "昴帮助爱蜜莉雅找回徽章"
    }
  ]
}
```

**推理规则**:
- 🤝 **关系影响**: 关系不好的角色之间达成合作的概率较低
- ⚔️ **战力约束**: 战斗力弱的角色战胜战斗力强的角色概率较低
- 🎭 **性格一致**: 角色行为必须符合其性格特质
- 🔗 **强度影响**: 关系强度影响角色间的互动方式

### 4. 世界线分支系统

**双分支设计**:
- **canon分支**: 保存原始世界线数据，不可修改
- **user_branch分支**: 保存用户修改后的数据

**智能分支选择**:
```python
# 系统自动判断保存分支
if user_has_edited or edit_count > 0:
    worldline_id = "user_branch"  # 有修改 → user_branch
else:
    worldline_id = "canon"        # 无修改 → canon
```

**数据保护**:
- 🛡️ **原始保护**: canon分支数据永不覆盖
- 🔄 **增量更新**: user_branch基于canon进行增量更新
- 📊 **对比分析**: 支持canon与user_branch的状态对比

## 📊 数据格式详解

### 章节状态快照

```json
{
  "chapter_id": 1,
  "title": "第1章",
  "events": [
    {
      "who": "昴",
      "action": "醒来",
      "target": null,
      "goal": "了解现状",
      "polarity": 0,
      "time": null,
      "location": "异世界",
      "precond": null,
      "effect": "开始冒险"
    }
  ],
  "relations": [
    {
      "a": "昴",
      "b": "爱蜜莉雅",
      "type": "同伴",
      "score": 0.8
    }
  ],
  "goals": {
    "昴": ["保护爱蜜莉雅", "解开死亡回归之谜"]
  },
  "objects": {
    "死亡回归": "已激活",
    "徽章": "爱蜜莉雅持有"
  },
  "meta": {
    "worldline_id": "canon",
    "model": "gpt-4o"
  }
}
```

### TKG四元组流

```jsonl
{"tau": "ch001_e1", "h": "昴", "r": "醒来", "t": "异世界", "meta": {"location": "异世界", "polarity": 0.0, "evidence": "昴在异世界醒来"}}
{"tau": "ch001_e2", "h": "昴", "r": "遇到", "t": "爱蜜莉雅", "meta": {"location": "王都", "polarity": 0.5, "evidence": "昴在王都遇到了银发少女爱蜜莉雅"}}
{"tau": "ch001_e3", "h": "昴", "r": "帮助", "t": "爱蜜莉雅", "meta": {"location": "王都", "polarity": 0.8, "evidence": "昴帮助爱蜜莉雅找回徽章"}}
```

### 人物图数据

**角色属性表**:
```json
{
  "chapter_id": 1,
  "characters": {
    "昴": {
      "combat_power": "弱",
      "inventory": ["徽章"],
      "traits": ["冲动", "守信"]
    },
    "爱蜜莉雅": {
      "combat_power": "中",
      "inventory": [],
      "traits": ["善良", "坚强"]
    }
  }
}
```

**关系图**:
```json
{
  "chapter_id": 1,
  "nodes": ["昴", "爱蜜莉雅", "雷姆"],
  "edges": [
    {
      "a": "昴",
      "b": "爱蜜莉雅",
      "type": "同伴",
      "score": 0.8,
      "evidence": "昴帮助爱蜜莉雅找回徽章"
    }
  ]
}
```

## 🎯 使用场景

### 1. 故事创作与编辑

```bash
# 启动创作模式
python narrative_agent.py

# 查看当前剧情
n/next          # 逐chunk播放

# 进行章节级编辑
ce 【昴】我决定更加谨慎地行动，先观察周围的环境

# 保存修改状态
state           # 保存到user_branch分支

# 查看生成的数据
tkg             # 查看TKG摘要
graph           # 查看人物图摘要
```

### 2. 数据分析与研究

```python
# 加载TKG数据进行分析
import json

with open("tkg/canon/chapter_001.tkg.jsonl", "r") as f:
    for line in f:
        triple = json.loads(line)
        print(f"{triple['h']} --{triple['r']}--> {triple['t']}")

# 分析人物关系网络
with open("graphs/canon/chapter_001.relations.json", "r") as f:
    relations = json.load(f)
    for edge in relations["edges"]:
        print(f"{edge['a']} --{edge['type']}--> {edge['b']} (强度: {edge['score']})")
```

### 3. 事件可行性判定

```python
from event_feasibility import plan_event_feasibility

# 判定事件可行性
event = "昴单挑猎肠者"
result = plan_event_feasibility(event, characters_graph, relations_graph)
print(f"可行性: {result.ok}, 评分: {result.score}")
print(f"理由: {result.reasons}")
```

## 🔧 高级配置

### 1. 词汇表配置

**性格特质词汇表** (`config/trait_vocab.json`):
```json
{
  "traits": ["勇敢", "谨慎", "聪明", "善良", "邪恶", "忠诚", "背叛"],
  "trait_descriptions": {
    "勇敢": "面对危险时表现勇敢",
    "谨慎": "做事小心谨慎"
  }
}
```

**关系类型词汇表** (`config/relation_vocab.json`):
```json
{
  "relation_types": ["信任", "同伴", "对立", "亲密", "仇恨"],
  "relation_descriptions": {
    "信任": "相信对方的能力或品格",
    "同伴": "共同行动的伙伴关系"
  }
}
```

### 2. 图更新规则

**图更新规则** (`config/graph_update_rules.yaml`):
```yaml
character_updates:
  - rule: "战斗力变化"
    condition: "角色经历重要战斗"
    action: "更新combat_power"
  
  - rule: "物品获得"
    condition: "角色获得新物品"
    action: "添加到inventory"

relation_updates:
  - rule: "关系深化"
    condition: "角色间互动增加"
    action: "提高关系强度"
```

## 🧪 测试与验证

### 1. 功能测试

```bash
# 测试数据抽取
python -c "from state_extractor import extract_state_for_chapter; print('✅ 抽取器正常')"

# 测试数据模型
python -c "from tkg_models import TKGEntry; print('✅ 数据模型正常')"

# 测试主程序
python -c "from narrative_agent import NarrativeAgent; print('✅ 主程序正常')"
```

### 2. 集成测试

```bash
# 运行完整测试流程
python narrative_agent.py

# 测试命令序列
# 1. 查看内容: n/next
# 2. 进行编辑: ce 【昴】测试内容
# 3. 保存状态: state
# 4. 查看数据: tkg, graph
```

### 3. 数据质量验证

```bash
# 验证JSON格式
python -c "import json; json.load(open('world_graph/canon/chapter_001.json')); print('✅ JSON格式正确')"

# 验证Pydantic模型
python -c "from tkg_models import CharactersSnapshot; import json; data=json.load(open('graphs/canon/chapter_001.characters.json')); CharactersSnapshot(**data); print('✅ 数据模型验证通过')"
```

## 🚨 注意事项

### 1. API密钥管理

- **必需**: 首次运行需要OpenAI API密钥生成canon数据
- **可选**: 无API密钥时系统会生成空状态，但文件结构正确
- **安全**: API密钥通过环境变量管理，不会硬编码在代码中

### 2. 数据备份

- **自动备份**: 系统会自动创建canon分支作为原始数据备份
- **手动备份**: 建议定期备份 `world_graph/` 目录
- **版本控制**: 建议将配置文件纳入版本控制，数据文件除外

### 3. 性能优化

- **缓存机制**: 系统会缓存已加载的人物数据
- **增量更新**: 只更新变化的部分，提高效率
- **重试机制**: LLM调用失败时自动重试，提高稳定性

### 4. 扩展性考虑

- **模块化设计**: 各功能模块独立，便于扩展
- **配置驱动**: 通过配置文件控制行为，无需修改代码
- **标准化接口**: 使用Pydantic模型确保数据一致性

## 🔮 未来规划

### 短期目标

- [ ] **事件可行性判定**: 基于人物数据判定事件合理性
- [ ] **世界线路由**: 智能推荐剧情发展方向
- [ ] **桥接生成**: 自动生成章节间的过渡内容

### 中期目标

- [ ] **多章节支持**: 扩展到多章节故事管理
- [ ] **可视化界面**: 开发Web界面进行可视化编辑
- [ ] **协作功能**: 支持多人协作创作

### 长期目标

- [ ] **AI编剧助手**: 基于TKG的智能编剧建议
- [ ] **故事质量评估**: 自动评估故事质量和连贯性
- [ ] **跨媒体适配**: 支持小说、剧本、游戏等多种形式

## 🤝 贡献指南

### 开发环境

```bash
# 克隆项目
git clone <repository-url>
cd World_developer

# 安装开发依赖
pip install -r requirements.txt

# 运行测试
python -m pytest tests/
```

### 代码规范

- **类型注解**: 使用Python类型注解
- **文档字符串**: 为所有函数添加文档字符串
- **测试覆盖**: 新功能需要包含测试用例
- **代码格式化**: 使用black进行代码格式化

### 提交规范

```
feat: 添加新功能
fix: 修复bug
docs: 更新文档
style: 代码格式调整
refactor: 代码重构
test: 添加测试
chore: 构建过程或辅助工具的变动
```

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- **OpenAI**: 提供强大的GPT-4o模型支持
- **Pydantic**: 提供优秀的数据验证框架
- **社区贡献者**: 感谢所有为项目做出贡献的开发者

---

**🎭 开始您的智能故事创作之旅吧！**

```bash
python narrative_agent.py
```
>>>>>>> 62899eb (Initial commit)

