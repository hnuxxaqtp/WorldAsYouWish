# 长期记忆系统文档

## 概述

长期记忆系统为每个角色提供基于向量检索的智能记忆功能，使角色能够记住过去的对话、事件、行动和观察。这些记忆会在角色生成规划、对话生成、事件生成和自动故事续写时被检索并用于保持行为一致性和故事连贯性。

## 模型管理

### 模型存储位置

模型默认存储在项目根目录下的 `model` 文件夹中：

- **Windows**: `C:\Users\TP\Desktop\World-Developer-main\World-Developer-main\model\paraphrase-multilingual-MiniLM-L12-v2--sentence_bert_config.json`
- **路径结构**:
  ```
  World-Developer-main/
  └── model/
      └── paraphrase-multilingual-MiniLM-L12-v2--sentence_bert_config.json/
          ├── config_sentence_transformers.json
          ├── modules.json
          ├── model.safetensors  (或 .bin)
          ├── tokenizer.json
          ├── tokenizer_config.json
          └── ...
  ```

### 首次下载模型

使用提供的下载脚本：

```bash
# 从项目根目录运行
python download_model.py
```

这将：
1. 从 huggingface.co 下载模型（需要网络）
2. 保存到 `[项目目录]/model/paraphrase-multilingual-MiniLM-L12-v2--sentence_bert_config.json`
3. 显示下载进度和文件大小

**注意**：首次下载需要约 400-500MB，可能需要几分钟时间。

### 从本地缓存复制（如果之前已下载）

如果你之前已经下载过此模型，可以直接从缓存复制到项目目录：

```bash
# Windows - 从用户缓存复制到项目目录
xcopy /E /I /Y %USERPROFILE%\.cache\torch\sentence_transformers\models\paraphrase-multilingual-MiniLM-L12-v2--sentence_bert_config.json "C:\Users\TP\Desktop\World-Developer-main\World-Developer-main\model\paraphrase-multilingual-MiniLM-L12-v2--sentence_bert_config.json"

# 或手动复制文件夹
# 源路径: C:\Users\TP\.cache\torch\sentence_transformers\models\paraphrase-multilingual-MiniLM-L12-v2--sentence_bert_config.json
# 目标路径: C:\Users\TP\Desktop\World-Developer-main\World-Developer-main\model\paraphrase-multilingual-MiniLM-L12-v2--sentence_bert_config.json
```

### 自定义模型路径

如果需要使用不同的模型目录，可以在初始化时指定：

```python
# 在 backend/main.py 中修改
memory_system = MemorySystem(
    model_name="paraphrase-multilingual-MiniLM-L12-v2",
    model_dir="D:/MyModels"  # 自定义路径
)
```

## 系统架构

### 后端组件

#### 1. `memory_system.py` - 记忆系统核心
- **Memory** 类：表示单条记忆
- **MemorySystem** 类：管理角色记忆的主类

#### 2. 集成点
- **agent_system.py**: 在生成角色规划和对话时检索相关记忆
- **main.py**: 提供记忆管理API接口

### 前端组件

#### 1. `MemoryPanel.jsx` - 记忆查看面板
- 查看角色的所有记忆
- 按类型筛选记忆（对话/事件/行动/观察）
- 搜索相关记忆（基于语义相似度）
- 添加自定义记忆

#### 2. 集成点
- **CharacterPanel.jsx**: 添加了"记忆"按钮，点击可打开记忆面板

## 记忆类型

| 类型 | 图标 | 说明 | 示例 |
|------|------|------|------|
| dialogue | 💬 | 对话记忆 | "我对李四说：关于魔法的知识" |
| event | 📅 | 事件记忆 | "在图书馆发现了一本古老魔法书" |
| action | ⚡ | 行动记忆 | "我决定探索古老的遗迹" |
| observation | 👁️ | 观察记忆 | "李四在训练场练习剑术，看起来很生气" |

## API 端点

### 1. 添加记忆
```
POST /api/memory/add
```

**请求体：**
```json
{
  "character_name": "张三",
  "content": "我和李四进行了对话，讨论了关于魔法的知识",
  "memory_type": "dialogue",
  "metadata": {
    "listener": "李四",
    "topic": "魔法知识"
  }
}
```

### 2. 获取角色所有记忆
```
GET /api/memory/{character_name}
```

**响应：**
```json
{
  "character_name": "张三",
  "count": 10,
  "memories": [
    {
      "content": "...",
      "memory_type": "dialogue",
      "timestamp": "2025-12-25T15:00:00",
      "metadata": {...}
    }
  ]
}
```

### 3. 获取最近记忆
```
GET /api/memory/{character_name}/recent?count=10&memory_types=dialogue,event
```

### 4. 搜索记忆（向量检索）
```
POST /api/memory/{character_name}/search
```

**请求体：**
```json
{
  "query": "图书馆 魔法书",
  "top_k": 5,
  "memory_types": ["action", "observation"],
  "min_similarity": 0.3
}
```

**响应返回最相关的记忆，按相似度降序排序**

### 5. 清除角色记忆
```
DELETE /api/memory/{character_name}
```

### 6. 保存所有记忆到磁盘
```
POST /api/memory/persist
```

## 使用示例

### 1. 角色规划时自动使用记忆

当角色生成计划时，系统会自动检索相关的记忆：

```python
# 在 agent_system.py 的 generate_plan 方法中
relevant_memories = memory_system.retrieve_memories(
    character_name=self.name,
    query=f"当前目标: {' '.join(self.goals)}",
    top_k=5
)
memory_text = memory_system.format_memories_for_prompt(relevant_memories)
```

这些记忆会被加入到 LLM 提示词中，帮助角色做出更一致的决定。

### 2. 对话时自动保存记忆

当角色进行对话时，系统会自动保存对话记忆，并立即写入磁盘：

```python
# 在 main.py 的对话生成端点中
memory_system.add_memory(
    character_name=request.speaker,
    content=f"我对 {request.listener} 说：{dialogue['content']}",
    memory_type="dialogue",
    metadata={
        "listener": request.listener,
        "topic": request.topic,
        "tone": dialogue.get("tone", ""),
        "intent": dialogue.get("intent", "")
    }
)
# ✅ 记忆会自动保存到磁盘，无需额外调用
```

### 3. 前端查看和搜索记忆

用户可以通过角色面板的"记忆"按钮打开记忆面板：
- 查看所有历史记忆
- 按类型筛选
- 使用语义搜索找到相关记忆
- 手动添加自定义记忆

### 4. 自动故事续写时使用记忆

在自动写故事功能中，系统会根据最近事件的内容智能检索相关记忆：

```python
# 在 main.py 的 /api/story/continue 端点中
# 从最近事件中提取角色名，查找相关记忆
relevant_memories = []
query_texts = [ev.get("description", "") for ev in recent_events[-3:]]
for query in query_texts:
    if query:
        memories = memory_system.retrieve_memories(name, query, top_k=2)
        for mem in memories:
            if mem not in relevant_memories:
                relevant_memories.append(mem)
```

这些相关记忆会被加入到故事续写的提示词中，使：
- 故事内容与角色过去的经历保持一致
- 续写的情节能够呼应之前发生的事件
- 角色的反应基于其记忆中的经验
- 故事发展具有更强的连贯性

## 技术细节

### 向量嵌入

使用 `sentence-transformers` 模型将文本转换为向量嵌入：

- **模型**: `paraphrase-multilingual-MiniLM-L12-v2`
- **特点**: 支持多种语言（包括中文），轻量高效
- **相似度计算**: 使用余弦相似度

### 存储格式

记忆以 JSONL 格式存储在 `memory_storage/{character_name}/memories.jsonl` 中：

```
{"character_name": "张三", "content": "...", "memory_type": "dialogue", "timestamp": "...", "metadata": {...}, "embedding": [0.1, 0.2, ...]}
```

### 初始化流程

1. 后端启动时自动初始化 `MemorySystem`
2. 从磁盘加载已保存的记忆
3. 将 `MemorySystem` 实例传递给 `AgentSystem`
4. 所有智能体共享同一个记忆系统实例

## 依赖项

```txt
sentence-transformers>=2.2.0
numpy>=1.24.0
```

## 测试

运行测试脚本：

```bash
cd backend
python test_memory.py
```

测试内容包括：
- 初始化记忆系统
- 添加不同类型的记忆
- 向量检索功能
- 获取最近记忆
- 格式化记忆用于提示词
- 保存到磁盘
- 从磁盘加载
- 清除记忆

## 最佳实践

### 1. 记忆粒度
- **细粒度**: 每条记忆应该包含一个独立的想法或事件
- **避免过长**: 保持记忆简洁，便于检索和理解

### 2. 元数据使用
- 记忆的元数据用于提供额外的上下文信息
- 关键元数据：参与者、地点、时间、对象、情感等

### 3. 搜索优化
- 使用具体的查询关键词
- 设置合适的 `top_k` 值（通常 5-10）
- 设置合理的 `min_similarity` 阈值（0.3-0.5）

### 4. 记忆管理
- 记忆在添加时会自动保存到磁盘（无需手动调用保存接口）
- `/api/memory/persist` 端点仍然保留，用于手动强制保存所有记忆
- 根据需要清除过时的记忆
- 可以设置记忆的最大数量和过期时间

## 文件结构

```
World-Developer-main/
├── backend/
│   ├── memory_system.py       # 记忆系统核心实现
│   ├── agent_system.py        # 集成记忆到智能体
│   ├── main.py               # 记忆管理API端点
│   ├── test_memory.py        # 记忆系统测试脚本
│   └── memory_storage/       # 记忆存储目录
│       └── {character_name}/
│           └── memories.jsonl
├── model/                    ⬅️ 模型存储目录
│   └── paraphrase-multilingual-MiniLM-L12-v2--sentence_bert_config.json/
│       ├── config_sentence_transformers.json
│       ├── modules.json
│       ├── model.safetensors
│       ├── tokenizer.json
│       └── ...
├── download_model.py         ⬅️ 模型下载脚本
└── frontend/
    └── src/
        └── components/
            ├── MemoryPanel.jsx       # 记忆面板组件
            └── MemoryPanel.css       # 记忆面板样式
```

## 故障排查

### 问题：模型文件不存在
**现象**：
```
❌ 错误：模型目录不存在
提示：请先下载模型到指定目录
```

**解决方案**：
1. 运行下载脚本：`python download_model.py`
2. 或手动下载模型到 `[项目目录]/model/paraphrase-multilingual-MiniLM-L12-v2--sentence_bert_config.json/`

### 问题：记忆模型加载缓慢
**解决方案**：
- 模型已存储在本地，首次加载约 2-5 秒
- 可以使用更小的模型如 `all-MiniLM-L6-v2`（约 200MB）

### 问题：检索结果不相关
**解决方案**：
- 调整 `min_similarity` 阈值
- 使用更具体的查询词
- 增加记忆的详细度和元数据

### 问题：内存占用过高
**解决方案**：
- 定期清除不重要的记忆
- 设置记忆的最大数量限制
- 使用批处理方式保存和加载

## 未来扩展

1. **记忆重要性评分**: 自动评估记忆的重要性，优先保留重要记忆
2. **记忆遗忘机制**: 模拟人类记忆遗忘，逐渐降低旧记忆的权重
3. **多模态记忆**: 支持图像、音频等多媒体记忆
4. **记忆关联网络**: 构建记忆之间的关联关系图
5. **增量学习**: 根据新的经验更新记忆向量和检索策略