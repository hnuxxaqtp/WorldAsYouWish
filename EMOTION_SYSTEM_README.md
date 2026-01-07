# 角色情感系统文档

## 概述

角色情感系统为每个角色提供动态情感模型，使角色能够根据事件和对话改变情绪状态。情感会影响角色的对话风格和行为决策，让故事角色更加生动和真实。

## 核心功能

1. **动态情感状态**：每个角色具有主要情感和次要情感，带有强度值（0.0 - 1.0）
2. **情感触发器**：根据关键词自动识别触发特定情感
3. **情感衰减**：情感会随时间逐渐回归中性状态
4. **情感历史**：记录角色的情感变化历程
5. **情感影响**：情感会影响角色对话的语气和表达方式

## 模型架构

### 基本情感类型

| 情感类型 | 图标 | 说明 |
|---------|------|------|
| HAPPY | 😊 | 快乐 |
| SAD | 😢 | 悲伤 |
| ANGRY | 😠 | 愤怒 |
| FEAR | 😨 | 恐惧 |
| SURPRISE | 😲 | 惊讶 |
| DISGUST | 🤢 | 厌恶 |
| NEUTRAL | 😐 | 平静 |
| ANXIOUS | 😰 | 焦虑 |
| CONFIDENT | 😎 | 自信 |
| TIRED | 😴 | 疲惫 |

### 情感状态结构

```python
{
  "primary_emotion": "快乐",      # 主要情感
  "intensity": 0.75,               # 强度 0.0-1.0
  "secondary_emotion": "平静",    # 次要情感
  "secondary_intensity": 0.3,      # 次要情感强度
  "last_updated": "2025-12-26T03:14:00",  # 最后更新时间
  "history": [...]                # 情感变化历史
}
```

## 后端组件

### 1. emotion_system.py

#### EmotionType 枚举
定义所有基本情感类型

#### EmotionState 类
表示单个角色的情感状态
- `to_dict()`: 转换为字典
- `from_dict()`: 从字典创建
- `add_history()`: 添加情感变化历史

#### EmotionTrigger 类
情感触发器配置
- `trigger_type`: 触发类型 (dialogue/event/action/observation)
- `keywords`: 触发关键词列表
- `target_emotion`: 触发的目标情感
- `intensity_change`: 强度变化值 (-1.0 到 1.0)
- `decay_rate`: 衰减率

#### EmotionSystem 类
情感系统管理器
- `initialize_character()`: 初始化角色情感状态
- `get_emotion_state()`: 获取角色情感状态
- `process_trigger()`: 处理情感触发
- `apply_emotion_decay()`: 应用情感衰减
- `get_emotion_influence_on_dialogue()`: 获取情感对对话的影响描述

### 2. 集成点

#### agent_system.py
- CharacterAgent 构造函数接受 emotion_system 参数
- `get_character_prompt()` 方法包含情感状态信息
- `generate_dialogue()` 方法使用情感影响描述

#### main.py
- 启动时初始化情感系统
- 对话生成时自动处理情感触发
- 事件生成时自动处理参与者的情感触发
- 返回情感变化信息

## API 接口

### 1. 获取角色情感状态
```
GET /api/emotions/{character_name}
```

**响应示例：**
```json
{
  "primary_emotion": "快乐",
  "intensity": 0.75,
  "secondary_emotion": "平静",
  "secondary_intensity": 0.3,
  "last_updated": "2025-12-26T03:14:00",
  "history": [
    {
      "emotion": "快乐",
      "intensity": 0.75,
      "cause": "dialogue: 我对 李四 说：谢谢你的帮助！",
      "timestamp": "2025-12-26T03:14:00"
    }
  ]
}
```

### 2. 获取所有角色的情感状态
```
GET /api/emotions
```

### 3. 应用情感衰减
```
POST /api/emotions/decay
```

**请求体：**
```json
{
  "character_name": "张三",
  "decay_factor": 0.1
}
```

### 4. 手动处理情感触发
```
POST /api/emotions/process-trigger
```

**参数：**
- `character_name`: 角色名称
- `trigger_type`: 触发类型
- `content`: 内容
- `metadata`: 额外元数据（可选）

## 前端组件

### CharacterPanel.jsx

#### 情感显示功能
1. **卡片预览**：显示主要情感、情感图标和强度
2. **详情面板**：完整的情感状态和历史记录
3. **强度可视化**：使用颜色和进度条表示强度
4. **历史追踪**：显示最近5条情感变化记录

#### 情感图标映射
```javascript
getEmotionEmoji(emotionType) {
  const emojiMap = {
    '快乐': '😊',
    '悲伤': '😢',
    '愤怒': '😠',
    '恐惧': '😨',
    '惊讶': '😲',
    '厌恶': '🤢',
    '平静': '😐',
    '焦虑': '😰',
    '自信': '😎',
    '疲惫': '😴'
  }
  return emojiMap[emotionType] || '😐'
}
```

#### 强度颜色映射
```javascript
getIntensityColor(intensity) {
  if (intensity > 0.7) return '#ff4444'    // 高强度：红色
  if (intensity > 0.4) return '#ffaa00'    // 中强度：橙色
  return '#44aaff'                          // 低强度：蓝色
}
```

### CharacterPanel.css

新增样式类：
- `.character-emotions`: 卡片中的情感显示区域
- `.emotion-main`: 主要情感信息
- `.emotion-secondary`: 次要情感信息
- `.emotion-detail`: 详情面板中的情感区域
- `.emotion-row`: 情感行布局
- `.intensity-bar`: 强度进度条
- `.emotion-history`: 情感历史记录

支持暗黑模式样式。

## 默认情感触发器

系统预置了多种情感触发器，按情感类型分类：

### 正向情感
```python
EmotionTrigger("dialogue", ["感谢", "谢谢", "高兴", "开心", "喜欢", "爱", "赞美"], 
             EmotionType.HAPPY, 0.3)
EmotionTrigger("dialogue", ["成功", "胜利", "赢了", "做到", "完成"], 
             EmotionType.CONFIDENT, 0.25)
EmotionTrigger("event", ["胜利", "成功", "庆典", "奖励"], 
             EmotionType.HAPPY, 0.35)
```

### 负向情感
```python
EmotionTrigger("dialogue", ["讨厌", "恨", "愤怒", "生气", "滚", "去死"], 
             EmotionType.ANGRY, 0.4)
EmotionTrigger("dialogue", ["害怕", "恐惧", "担心", "担忧", "危险"], 
             EmotionType.FEAR, 0.3)
EmotionTrigger("dialogue", ["难过", "悲伤", "伤心", "哭", "痛苦"], 
             EmotionType.SAD, 0.35)
EmotionTrigger("event", ["失败", "死亡", "损失", "伤害"], 
             EmotionType.SAD, 0.4)
EmotionTrigger("event", ["攻击", "威胁", "危险"], 
             EmotionType.FEAR, 0.35)
```

### 其他情感
```python
EmotionTrigger("dialogue", ["惊讶", "意外", "不敢相信", "怎么可能"], 
             EmotionType.SURPRISE, 0.3)
EmotionTrigger("dialogue", ["恶心", "厌恶", "受不了"], 
             EmotionType.DISGUST, 0.35)
EmotionTrigger("event", ["战斗", "劳动", "长途"], 
             EmotionType.TIRED, 0.2)
```

## 情感处理流程

### 对话生成时
1. 生成角色对话内容
2. 保存对话记忆
3. 分析对话内容，查找匹配的情感触发器
4. 更新说话者的情感状态
5. 如果对话涉及倾听者，可能更新倾听者的情感
6. 返回情感变化信息

### 事件生成时
1. 生成事件内容
2. 保存事件记忆给所有参与者
3. 分析事件内容，查找匹配的情感触发器
4. 更新所有参与者的情感状态
5. 返回情感变化信息

### 情感对对话的影响
当角色处于特定情感状态时，对话生成会收到影响：

- **快乐**: 语气轻松愉快，言辞积极
- **悲伤**: 语气低沉，言辞悲伤
- **愤怒**: 语气激动，可能带有攻击性
- **恐惧**: 语气紧张，显得担忧
- **自信**: 语气坚定，充满信心
- **疲惫**: 语气疲惫，反应迟缓

影响程度取决于情感强度：
- > 0.7: 情感非常强烈，明显影响说话方式
- > 0.4: 情感较为明显，轻微影响说话方式
- < 0.4: 情感较为微弱，对说话方式影响较小

## 自定义情感触发器

可以通过代码添加自定义触发器：

```python
# 在 emotion_system.py 中或运行时添加
emotion_system.add_custom_trigger(
    trigger_type="dialogue",
    keywords=["魔法", "法术", "咒语"],
    target_emotion="兴奋",
    intensity_change=0.35,
    decay_rate=0.1
)
```

## 情感衰减机制

情感会随时间逐渐回归中性状态：

1. 调用衰减 API 或定期自动衰减
2. 强度按衰减系数减少：`new_intensity = old_intensity * (1.0 - decay_factor)`
3. 当强度低于 0.1 时，回归中性状态
4. 默认衰减系数为 0.1

## 工作流程示例

### 场景1：角色之间的对话

```javascript
// 1. 用户选择说话者和倾听者
const dialogue = await axios.post('/api/dialogue', {
  speaker: '张三',
  listener: '李四',
  topic: '感谢帮助',
  content: '谢谢你的帮助！'
})

// 2. 响应包含对话内容和情感变化
{
  "dialogue": {
    "content": "谢谢你的帮助！",
    "tone": "感激",
    "intent": "表达感谢"
  },
  "emotion_changes": [
    {
      "character_name": "张三",
      "old_emotion": "平静",
      "new_emotion": "快乐",
      "old_intensity": 0.5,
      "new_intensity": 0.75,
      "trigger_cause": "dialogue: 谢谢你的帮助！"
    }
  ]
}

// 3. 前端更新情感显示
```

### 场景2：事件发生影响多个角色

```javascript
// 1. 生成事件
const event = await axios.post('/api/events/generate', {
  location: '图书馆',
  participants: ['张三', '李四'],
  event_type: '发现'
})

// 2. 响应包含事件和多个角色的情感变化
{
  "event": {
    "title": "发现魔法书",
    "description": "在图书馆发现了一本古老的魔法书",
    "type": "discovery"
  },
  "emotion_changes": [
    {
      "character_name": "张三",
      "new_emotion": "惊讶",
      "new_intensity": 0.6
    },
    {
      "character_name": "李四",
      "new_emotion": "惊讶",
      "new_intensity": 0.55
    }
  ]
}
```

## 最佳实践

### 1. 触发器设计
- 使用具体、明确的关键词
- 根据故事背景调整触发器
- 避免关键词过于通用导致误触发

### 2. 强度设置
- 正向事件通常使用 0.3-0.4 的强度
- 负向事件可能使用 0.4-0.5 的强度（影响更大）
- 极端情绪（如恐惧、愤怒）谨慎使用高强度

### 3. 衰减管理
- 定期应用情感衰减，保持新鲜感
- 在世界时间推进时自动衰减
- 重要角色的情感可以保持更久

### 4. 情感历史
- 定期清理旧的历史记录
- 保留最近的变化用于分析和调试
- 可以基于历史分析角色情感模式

## 故障排查

### 问题：角色情感没有更新
**解决方案：**
1. 检查情感系统是否正确初始化
2. 确认对话或事件内容包含触发关键词
3. 查看 API 返回的 emotion_changes
4. 检查前端是否正确处理新的情感数据

### 问题：情感变化过于频繁
**解决方案：**
1. 调整触发器的关键词，减少匹配
2. 降低 intensity_change 值
3. 增加情感衰减频率
4. 使用更具体的关键词

### 问题：情感影响对话效果不明显
**解决方案：**
1. 检查情感强度是否足够高
2. 调整 get_emotion_influence_on_dialogue 的描述
3. 增加 LLM 温度参数，让模型更自由地表达情感
4. 查看生成的对话 tone 字段是否符合预期

## 未来扩展

1. **情感传播**：角色之间的情感可以相互影响
2. **情感持久化**：将情感状态保存到磁盘
3. **情感关联记忆**：情感与记忆关联，形成更丰富的角色心理模型
4. **多维度情感**：支持更复杂的情感空间（Plutchik 情感轮）
5. **情感冲突**：处理相互矛盾的情感状态
6. **情感驱动的行为**：情感直接影响角色行动选择

## 依赖项

无额外依赖，完全使用 Python 标准库。

## 文件结构

```
World-Developer-main/
├── backend/
│   ├── emotion_system.py       # 情感系统核心实现
│   ├── agent_system.py        # 集成情感到智能体
│   └── main.py               # 情感管理API端点
└── frontend/
    └── src/
        └── components/
            ├── CharacterPanel.jsx    # 情感UI显示
            └── CharacterPanel.css    # 情感样式
```

## 测试建议

1. 测试对话生成时情感是否正确触发
2. 测试事件影响多个角色时情感是否正确更新
3. 测试情感衰减是否正常工作
4. 测试不同强度对对话的影响
5. 测试前端情感显示是否正确更新

## 更新日志

### v1.0.0 (2025-12-26)
- 实现基础情感系统
- 支持基本情感类型
- 实现情感触发器机制
- 集成到对话和事件生成
- 添加情感管理 API
- 创建前端情感显示组件