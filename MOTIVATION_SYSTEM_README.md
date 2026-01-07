# 多层级动机系统文档

## 概述

多层级动机系统为角色添加了短期、中期和长期目标的层次结构，使角色的行为决策更加逻辑化和可预测。该系统允许角色的规划、对话和行动以动机驱动的方式进行，而不是完全随机生成。

## 系统架构

### 动机级别 (MotivationLevel)

动机分为三个级别，形成层次化的目标结构：

- **短期目标 (SHORT_TERM)**: 影响当前行动的即时目标（1-7天）
  - 示例：完成某个对话、探索特定位置、解决眼前问题
- **中期目标 (MEDIUM_TERM)**: 影响近期规划的目标（1-4周）
  - 示例：建立关系、完成一系列任务、提升某项技能
- **长期目标 (LONG_TERM)**: 角色的核心驱动力和人生目标（数月至数年）
  - 示例：守护某样东西、实现某种理想、改变世界状态

### 动机优先级 (MotivationPriority)

- **紧急 (CRITICAL)**: 必须立即处理的目标，如生命威胁
- **重要 (HIGH)**: 重要的但非紧急的目标
- **一般 (NORMAL)**: 常规目标，默认优先级
- **较低 (LOW)**: 可选择处理或不处理的目标

### 动机状态 (MotivationStatus)

- **PENDING (待定)**: 已创建但尚未开始
- **IN_PROGRESS (进行中)**: 正在积极追求此目标
- **PAUSED (暂停)**: 暂时搁置（遇到阻碍或资源不足）
- **COMPLETED (已完成)**: 目标已达成
- **FAILED (失败)**: 目标无法完成
- **ABANDONED (放弃)**: 主动放弃此目标

### Motivation 类

```python
class Motivation:
    def __init__(
        self,
        description: str,           # 动机描述
        level: MotivationLevel,     # 动机级别
        priority: MotivationPriority = MotivationPriority.NORMAL,
        status: MotivationStatus = MotivationStatus.PENDING,
        deadline: Optional[str] = None,        # 截止日期
        progress: float = 0.0,                 # 进度 0.0-1.0
        sub_goals: Optional[List[str]] = None, # 子目标列表
        blockers: Optional[List[str]] = None,  # 阻碍因素
        prerequisites: Optional[List[str]] = None, # 前置动机ID
        metadata: Optional[Dict] = None        # 额外元数据
    )
```

### MotivationSystem 类

管理所有角色的动机，提供完整的增删改查功能。

#### 主要方法

- `add_motivation(character_name: str, motivation: Motivation)`: 添加新动机
- `get_motivations_by_level(character_name: str, level: MotivationLevel)`: 按级别获取动机
- `get_active_motivations(character_name: str)`: 获取所有进行中的动机
- `update_progress(character_name: str, motivation_id: str, progress: float, note: str)`: 更新进度
- `complete_motivation(character_name: str, motivation_id: str)`: 完成动机
- `add_blocker(character_name: str, motivation_id: str, blocker: str)`: 添加阻碍
- `remove_blocker(character_name: str, motivation_id: str, blocker: str)`: 移除阻碍
- `get_summary(character_name: str)`: 获取动机状态摘要
- `format_for_planning(character_name: str)`: 格式化动机信息供规划生成使用

## API 接口

### 1. 获取角色动机摘要
**GET** `/api/motivations/{character_name}`

返回角色的动机状态摘要，包括总数、各级别数量、完成率等。

```bash
curl http://localhost:8000/api/motivations/银发少女
```

响应示例：
```json
{
  "character": "银发少女",
  "total": 6,
  "by_level": {
    "短期": 2,
    "中期": 3,
    "长期": 1
  },
  "by_status": {
    "PENDING": 1,
    "IN_PROGRESS": 3,
    "PAUSED": 1,
    "COMPLETED": 1
  },
  "completion_rate": 0.1667,
  "active_motivations": [
    {
      "id": "[动机ID]",
      "description": "[动机描述]",
      "level": "SHORT_TERM",
      "priority": "紧急",
      "status": "IN_PROGRESS",
      "progress": 0.5
    }
  ]
}
```

### 2. 按级别获取动机
**GET** `/api/motivations/{character_name}/level/{level}`

获取指定级别的所有动机。

```bash
curl http://localhost:8000/api/motivations/银发少女/level/SHORT_TERM
```

### 3. 获取进行中的动机
**GET** `/api/motivations/{character_name}/active`

获取所有状态为 IN_PROGRESS 的动机。

```bash
curl http://localhost:8000/api/motivations/银发少女/active
```

### 4. 添加新动机
**POST** `/api/motivations/add`

为角色添加新的动机。

请求体：
```json
{
  "character_name": "银发少女",
  "motivation": {
    "description": "与旅行者建立友好关系",
    "level": "MEDIUM_TERM",
    "priority": "HIGH",
    "deadline": "2024-02-01",
    "sub_goals": [
      "进行第一次对话",
      "了解旅行者的目的",
      "分享一些秘密"
    ]
  }
}
```

### 5. 更新动机
**PUT** `/api/motivations/{character_name}/{motivation_id}`

更新动机的属性。

请求体（可部分更新）：
```json
{
  "description": "新描述",
  "priority": "CRITICAL",
  "status": "IN_PROGRESS"
}
```

### 6. 更新动机进度
**POST** `/api/motivations/{character_name}/{motivation_id}/progress`

更新动机的完成进度。

请求体：
```json
{
  "progress": 0.6,
  "note": "已与旅行者进行深入对话"
}
```

### 7. 完成动机
**POST** `/api/motivations/{character_name}/{motivation_id}/complete`

将动机标记为已完成，并自动激活依赖于它的后续动机。

### 8. 添加阻碍
**POST** `/api/motivations/{character_name}/{motivation_id}/blocker`

为动机添加阻碍因素，可能暂时暂停此动机。

请求体：
```json
{
  "blocker": "缺乏必要的资源或信息"
}
```

### 9. 删除动机
**DELETE** `/api/motivations/{character_name}/{motivation_id}`

放弃并删除指定动机。

## 集成到智能体系统

### 规划生成集成

动机信息被集成到角色规划生成过程中，使规划更加符合角色的目标导向。

在 `agent_system.py` 的 `generate_plan()` 方法中：

```python
# 获取动机信息
motivation_text = "当前无明确动机"
if self.motivation_system:
    motivation_text = self.motivation_system.format_for_planning(self.name)
```

生成示例文本：
```
当前动机:
【紧急】短期目标：
- 寻找失散的同伴 (50%)
  
【重要】中期目标：
- 揭开古老秘密 (30%)
- 建立信任关系 (70%)

【核心】长期目标：
- 守护世界的平衡
```

### 对话生成集成

可以在对话系统中访问角色的动机，使对话内容与当前目标保持一致。

### 事件生成集成

动机信息已集成到事件生成过程中，使生成的事件能够反映角色的目标追求。

在 `world_engine.py` 的 `generate_event()` 方法中：

```python
# 获取参与者的动机摘要
motivation_data = None
if self.motivation_system:
    motivation_data = self.motivation_system.get_motivation_summary(char_name)

participants_info.append({
    "name": char_name,
    "location": agent.location,
    "status": agent.status,
    "goals": agent.goals,
    "emotions": emotion_data,
    "motivations": motivation_data
})
```

事件生成prompt会特别强调：
- 角色的紧急和重要动机应该影响其行动选择
- 角色为实现目标会采取的具体行动
- 可以在事件描述中加入角色的内心独白展现动机

### 故事生成集成

动机信息已集成到自动故事续写功能中，使小说内容更加立体丰满。

在 `main.py` 的 `/api/story/continue` 端点中：

```python
# 收集参与角色的动机信息
if motivation_system:
    motivations = motivation_system.get_character_motivations(name)
    if motivations:
        active_mots = [m for m in motivations if m.status in [MotivationStatus.IN_PROGRESS, MotivationStatus.PENDING]]
        char_context += "主要目标：\n"
        for m in active_mots[:3]:
            priority_text = {...}.get(m.priority, "")
            level_text = {...}.get(m.level, "")
            char_context += f"  {priority_text}{level_text}：{m.description}（进度{m.progress*100:.0f}%）\n"
```

故事生成系统会：
1. 在续写前获取所有活跃角色的动机信息
2. 通过内心独白展现角色的目标追求
3. 让角色的行动与动机相呼应
4. 体现角色为达成目标付出的努力

## 默认动机模板

为常见角色类型提供预设动机模板。

### 守护者角色
```json
{
  "long_term": [
    {
      "description": "守护所在区域的和平与安全",
      "level": "LONG_TERM",
      "priority": "HIGH"
    }
  ],
  "medium_term": [
    {
      "description": "训练新成员",
      "level": "MEDIUM_TERM",
      "priority": "NORMAL"
    }
  ],
  "short_term": [
    {
      "description": "巡逻指定区域",
      "level": "SHORT_TERM",
      "priority": "NORMAL"
    }
  ]
}
```

### 探索者角色
```json
{
  "long_term": [
    {
      "description": "探索未知区域",
      "level": "LONG_TERM",
      "priority": "HIGH"
    }
  ],
  "medium_term": [
    {
      "description": "绘制地图",
      "level": "MEDIUM_TERM",
      "priority": "NORMAL"
    }
  ],
  "short_term": [
    {
      "description": "准备装备和补给",
      "level": "SHORT_TERM",
      "priority": "HIGH"
    }
  ]
}
```

### 学习者角色
```json
{
  "long_term": [
    {
      "description": "掌握某种古老技艺",
      "level": "LONG_TERM",
      "priority": "NORMAL"
    }
  ],
  "medium_term": [
    {
      "description": "寻找导师",
      "level": "MEDIUM_TERM",
      "priority": "HIGH"
    }
  ],
  "short_term": [
    {
      "description": "收集相关资料",
      "level": "SHORT_TERM",
      "priority": "NORMAL"
    }
  ]
}
```

## 最佳实践

### 1. 设置角色的初始动机

```python
from motivation_system import Motivation, MotivationLevel, MotivationPriority

# 创建长期核心动机
long_term = Motivation(
    description="守护世界的平衡不受破坏",
    level=MotivationLevel.LONG_TERM,
    priority=MotivationPriority.HIGHEST
)

# 创建中期目标
medium_term = Motivation(
    description="寻找传说中的神器",
    level=MotivationLevel.MEDIUM_TERM,
    priority=MotivationPriority.HIGH,
    prerequisites=[long_term.id]  # 依赖于长期动机
)

# 创建短期任务
short_term = Motivation(
    description="收集关于神器的线索",
    level=MotivationLevel.SHORT_TERM,
    priority=MotivationPriority.HIGH,
    prerequisites=[medium_term.id]
)

# 依次添加到系统
motivation_system.add_motivation("角色名", long_term)
motivation_system.add_motivation("角色名", medium_term)
motivation_system.add_motivation("角色名", short_term)
```

### 2. 动机链的依赖管理

动机的 `prerequisites` 参数可以创建依赖关系链：
- 当前置动机完成时，依赖它的后续动机会自动激活
- 这样可以确保角色按逻辑顺序追求目标

### 3. 使用阻碍和暂停机制

当角色遇到困难时，可以添加阻碍：

```python
motivation_system.add_blocker(
    "角色名",
    motivation_id,
    "需要获取通行密码"
)

# 这可能会自动将动机状态改为 PAUSED
```

### 4. 更新进度并添加备注

```python
motivation_system.update_progress(
    "角色名",
    motivation_id,
    progress=0.3,
    note="已获得第一条线索，正在追寻"
)
```

### 5. 定期审查和调整动机

根据剧情发展和角色成长，定期调整角色的动机：
- 完成过时的动机
- 添加新的动机
- 调整优先级

## 动机与记忆系统的协同

动机系统可以与记忆系统协同工作：

1. **基于记忆生成动机**: 分析角色的近期记忆，自动生成相关动机
   - 示例：角色与某人发生了冲突 → 生成动机"解决冲突"

2. **记忆与动机关联**: 在记忆中标注相关的动机ID
   - 示例：记忆"与旅行者建立联系" 关联到动机"与旅行者建立友好关系"

3. **动机完成记录**: 动机完成时自动创建记忆记录
   - 示例：完成"收集线索"后，创建记忆"已收集关键线索"

## 动机与情感系统的协同

动机的状态变化可以影响角色的情感：

- **动机达成**: 提升快乐和满足感
- **动机失败**: 增加悲伤或愤怒
- **遇到阻碍**: 增加焦虑或沮丧
- **放弃动机**: 可能引发失落或释然

## UI 显示

前端 `CharacterPanel` 组件现在会显示角色的动机信息：

1. **卡片摘要**: 显示各层级动机数量和完成率
2. **详细视图**: 显示所有动机的详细信息
   - 优先级颜色标识（红色=紧急，黄色=重要，蓝色=一般）
   - 进度条显示
   - 阻碍因素列表
   - 子目标列表

## 扩展功能建议

### 1. 动机持久化

将动机数据保存到磁盘，类似记忆系统：

```python
class MotivationSystem:
    def save_to_disk(self, character_name: str):
        """保存角色的动机到磁盘"""
        path = f"backend/motivation_storage/{character_name}/motivations.json"
        # 实现保存逻辑
```

### 2. 动机衰减系统

长期未完成的动机会逐渐降低优先级：

```python
def _apply_motivation_decay(self):
    """应用动机衰减"""
    for motivation in self.motivations.values():
        if motivation.status == MotivationStatus.IN_PROGRESS:
            # 根据时间推移降低优先级
            pass
```

### 3. 冲突检测

检测相互冲突的动机：

```python
def detect_conflicts(self, character_name: str) -> List[Dict]:
    """检测相互冲突的动机"""
    # 实现冲突检测逻辑
    pass
```

### 4. 动机生成AI

使用LLM自动生成符合角色性格和背景的动机：

```python
async def generate_motivations_for_character(self, character_name: str) -> List[Motivation]:
    """为角色自动生成动机"""
    # 基于角色属性和背景故事
    pass
```

## 测试

使用提供的API接口测试动机系统的各项功能：

```bash
# 1. 添加动机
curl -X POST http://localhost:8000/api/motivations/add \
  -H "Content-Type: application/json" \
  -d '{
    "character_name": "银发少女",
    "motivation": {
      "description": "测试动机",
      "level": "SHORT_TERM",
      "priority": "HIGH"
    }
  }'

# 2. 查看动机摘要
curl http://localhost:8000/api/motivations/银发少女

# 3. 更新进度
curl -X POST http://localhost:8000/api/motivations/银发少女/[ID]/progress \
  -H "Content-Type: application/json" \
  -d '{"progress": 0.5, "note": "进行到一半"}'

# 4. 完成动机
curl -X POST http://localhost:8000/api/motivations/银发少女/[ID]/complete

# 5. 删除动机
curl -X DELETE http://localhost:8000/api/motivations/银发少女/[ID]
```

## 故障排查

### 问题：动机未在规划生成中出现

**解决方案**：
1. 确认 `AgentSystem` 初始化时传入 `motivation_system`
2. 检查动机状态是否为 `IN_PROGRESS` 或 `PENDING`
3. 确认 `format_for_planning()` 返回的数据格式正确

### 问题：依赖链未正确激活

**解决方案**：
1. 确认 `prerequisites` 中的ID与实际动机ID匹配
2. 检查已完成动机的ID是否正确
3. 确认依赖的动机状态确实为 `COMPLETED`

### 问题：UI 未显示动机信息

**解决方案**：
1. 检查API端点是否正常返回数据
2. 确认角色名称正确传递
3. 检查浏览器控制台是否有错误
4. 验证前端是否正确处理返回的动机数据

## 总结

多层级动机系统为角色提供了目标驱动行为的能力，使角色的行为更加逻辑化和可预测。通过与记忆和情感系统的集成，可以创建出更加丰富和真实的行为模式。

系统遵循简洁的原则，提供了基础但完整的动机管理功能。根据项目需要，可以通过扩展添加更多高级特性。

## 相关文档

- [记忆系统文档](./MEMORY_SYSTEM_README.md)
- [情感系统文档](./EMOTION_SYSTEM_README.md)
- [项目主README](./README.md)