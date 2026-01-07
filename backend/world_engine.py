#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
世界引擎 - 负责世界推进和事件生成
"""

from typing import Dict, List, Optional, Any
from openai import OpenAI
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agent_system import AgentSystem
from emotion_system import EmotionSystem, EmotionType
from motivation_system import MotivationSystem
from npc_generator import NPCGenerator, NPCRole
import json


class WorldEngine:
    """世界引擎"""
    
    def __init__(
        self,
        client: Optional[OpenAI],
        agent_system: Optional[AgentSystem],
        emotion_system: Optional[EmotionSystem] = None,
        motivation_system: Optional[MotivationSystem] = None,
        npc_generator: Optional[NPCGenerator] = None
    ):
        self.client = client
        self.agent_system = agent_system
        self.emotion_system = emotion_system
        self.motivation_system = motivation_system
        self.npc_generator = npc_generator
        
        # 世界状态
        self.current_time = 0
        self.locations: Dict[str, Dict] = {}
        self.location_map: Dict[str, List[str]] = {}  # 地点连接关系
        self.recent_events: List[Dict] = []
        
        # 世界数据
        self.world_data: Optional[Dict] = None
    
    def initialize(self, world_data: Dict):
        """初始化世界"""
        self.world_data = world_data
        
        # 从世界数据提取地点信息
        self.locations = world_data.get("locations", {})
        self.location_map = world_data.get("location_map", {})
        
        # 初始化时间
        self.current_time = world_data.get("initial_time", 0)
        
        # 初始化事件历史
        self.recent_events = world_data.get("initial_events", [])
        
        print(f"✅ 世界引擎初始化完成: {len(self.locations)} 个地点")
    
    def get_world_context(self) -> Dict:
        """获取当前世界上下文"""
        context = {
            "current_time": self.current_time,
            "locations": self.locations,
            "recent_events": self.recent_events[-5:],  # 最近5个事件
        }
        
        # 添加角色状态
        if self.agent_system:
            context["characters"] = {
                name: {
                    "location": agent.location,
                    "status": agent.status,
                    "goals": agent.goals
                }
                for name, agent in self.agent_system.agents.items()
            }
        
        return context
    
    async def advance(
        self,
        time_steps: int = 1,
        focus_characters: Optional[List[str]] = None
    ) -> List[Dict]:
        """推进世界时间，生成新事件"""
        new_events = []
        
        for step in range(time_steps):
            self.current_time += 1
            
            # 生成新事件
            event = await self.generate_event(
                participants=focus_characters,
                event_type="world_advance"
            )
            
            if event:
                # generate_event 内部已经负责写入 self.recent_events，
                # 这里只收集返回给调用方的新增事件，避免时间线重复
                new_events.append(event)
        
        return new_events
    
    async def generate_event(
        self,
        location: Optional[str] = None,
        participants: Optional[List[str]] = None,
        event_type: Optional[str] = None
    ) -> Optional[Dict]:
        """生成事件"""
        if not self.client:
            event = {
                "time": self.current_time,
                "type": event_type or "world_event",
                "description": "（无LLM支持，无法生成事件）",
                "location": location or "未知",
                "participants": participants or []
            }
            # 也写入时间线，保证前后端视图一致
            self.recent_events.append(event)
            if len(self.recent_events) > 100:
                self.recent_events = self.recent_events[-100:]
            return event
        
        # 获取世界上下文
        world_context = self.get_world_context()
        
        # 获取参与者信息
        participants_info = []
        if participants and self.agent_system:
            for char_name in participants:
                agent = self.agent_system.get_agent(char_name)
                if agent:
                    # 获取情感状态
                    emotion_data = None
                    if self.emotion_system:
                        emotion_state = self.emotion_system.get_emotion_state(char_name)
                        if emotion_state:
                            emotion_data = emotion_state.to_dict()
                    
                    # 获取动机摘要
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
        
        prompt = f"""你是一个故事世界的事件生成器。根据当前世界状态和角色情况，生成一个合理的事件。

【世界状态】
当前时间: {self.current_time}
地点: {json.dumps(self.locations, ensure_ascii=False, indent=2)}

【本次事件指定地点】
本次事件如果提供了 location 参数，则**必须**让事件发生在该地点，并且在返回的 JSON 中：
- 将 location 字段设置为该地点的名称
- 事件描述中也要体现该地点的相关信息
本次调用的 location 参数为: {location or "未指定（则自行选择合理地点）"}

【参与者】
{json.dumps(participants_info, ensure_ascii=False, indent=2) if participants_info else "无特定参与者"}

【事件类型】
{event_type if event_type else "自然事件"}

【最近事件】
{json.dumps(self.recent_events[-3:], ensure_ascii=False, indent=2) if self.recent_events else "无"}

【任务】
生成一个符合世界状态的事件。事件应该：
1. 符合故事世界的设定
2. 与最近的事件有逻辑关联
3. 如果指定了参与者，事件应该涉及这些角色
4. 如果指定了地点，事件应该发生在该地点
5. 事件应该推动故事发展
6. 特别注意参与者的情感状态和动机，让事件反映其内心活动和目标追求
7. 如果参与者有强烈的情感（如愤怒、喜悦、恐惧），事件应体现这些情感对行为的影响
8. 如果参与者有活跃的动机（尤其是紧急或重要的目标），事件应展现其为目标采取的行动
9. 可以在描述中加入角色的内心独白来展现其情感和动机
10. **重要**：如果事件需要新的角色（如路人、店主、守卫等普通角色），请在generate_npc字段中使用简洁的关键词描述需要生成的角色类型（如"守卫"、"农夫"、"商人"等）。不要让主角与不存在的NPC互动，如果需要NPC参与事件，请先通过generate_npc字段生成。

请以JSON格式输出：
{{
  "time": {self.current_time},
  "type": "事件类型",
  "title": "事件标题",
  "description": "事件详细描述",
  "location": "事件发生地点",
  "participants": ["参与者1", "参与者2"],
  "consequences": ["后果1", "后果2"],
  "importance": "事件重要性（低/中/高）",
  "generate_npc": "NPC角色类型关键词（如守卫、农夫、商人等）或null"
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="Qwen/Qwen2.5-7B-Instruct",
                messages=[
                    {"role": "system", "content": "你是故事世界的事件生成器，负责生成符合世界设定的合理事件。只输出JSON，不要其他文字。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                response_format={"type": "json_object"}
            )
            
            event = json.loads(response.choices[0].message.content)
            event["time"] = self.current_time  # 确保时间正确
            
            # 如果需要生成新地点，则自动生成
            location_name = None
            if "generate_location" in event and event["generate_location"] and isinstance(event["generate_location"], dict):
                location_data = event["generate_location"]
                location_name = self.add_new_location(
                    name=location_data.get("name", ""),
                    location_type=location_data.get("type", "未知"),
                    description=location_data.get("description", "")
                )
                if location_name:
                    # 更新事件地点
                    event["location"] = location_name
                    # 更新描述以包含新地点
                    event["description"] = event["description"] + f"\n【系统自动生成新地点：{location_name}】"
                    print(f"✅ 自动生成新地点: {location_name}")
            
            # 如果需要生成NPC，则自动生成
            npc_name = None
            if "generate_npc" in event and event["generate_npc"]:
                role_hint = event["generate_npc"]
                npc_name = self.auto_generate_npc(location=event.get("location", "乡村"), role_hint=role_hint)
                if npc_name:
                    # 将生成的NPC名称添加到参与者列表
                    if "participants" not in event:
                        event["participants"] = []
                    event["participants"].append(npc_name)
                    # 更新描述以包含NPC名称
                    event["description"] = event["description"] + f"\n【系统自动生成NPC：{npc_name}】"
            
            # 写入时间线
            self.recent_events.append(event)
            if len(self.recent_events) > 100:
                self.recent_events = self.recent_events[-100:]
            return event
        except Exception as e:
            event = {
                "time": self.current_time,
                "type": event_type or "world_event",
                "title": "事件生成失败",
                "description": f"（事件生成失败: {str(e)}）",
                "location": location or "未知",
                "participants": participants or [],
                "consequences": [],
                "importance": "低"
            }
            # 即便失败也写入时间线，便于前端调试查看
            self.recent_events.append(event)
            if len(self.recent_events) > 100:
                self.recent_events = self.recent_events[-100:]
            return event
    
    def get_location_info(self, location_name: str) -> Optional[Dict]:
        """获取地点信息"""
        return self.locations.get(location_name)
    
    def get_characters_at_location(self, location_name: str) -> List[str]:
        """获取某个地点的所有角色"""
        if not self.agent_system:
            return []
        
        characters = []
        for name, agent in self.agent_system.agents.items():
            if agent.location == location_name:
                characters.append(name)
        
        return characters
    
    def add_new_location(self, name: str, location_type: str = "未知", description: str = "") -> Optional[str]:
        """添加新地点到世界"""
        if not name or not name.strip():
            return None
        
        # 规范化地名
        name = name.strip()
        
        # 检查是否已存在
        if name in self.locations:
            return name
        
        # 添加新地点
        self.locations[name] = {
            "name": name,
            "description": description or f"故事中发现的地点：{name}",
            "type": location_type
        }
        
        print(f"✅ 新地点已添加到世界: {name} ({location_type})")
        
        # 如果有世界数据，尝试更新到文件
        if hasattr(self, 'world_data') and self.world_data:
            self.world_data["locations"] = self.locations
        
        return name
    
    def auto_generate_npc(self, location: str = "乡村", role_hint: Optional[str] = None) -> Optional[str]:
        """自动生成NPC并添加到世界"""
        if not self.npc_generator or not self.agent_system:
            return None
        
        try:
            # 根据角色提示选择角色类型
            role = None
            if role_hint:
                # 简单的关键词匹配
                role_mapping = {
                    "店主": NPCRole.MERCHANT,
                    "商人": NPCRole.MERCHANT,
                    "卖货": NPCRole.MERCHANT,
                    "守卫": NPCRole.GUARD,
                    "卫兵": NPCRole.GUARD,
                    "武士": NPCRole.ADVENTURER,
                    "法师": NPCRole.SCHOLAR,
                    "学者": NPCRole.SCHOLAR,
                    "农夫": NPCRole.FARMER,
                    "农民": NPCRole.FARMER,
                    "医生": NPCRole.HEALER,
                    "治疗": NPCRole.HEALER,
                    "吟游诗人": NPCRole.BARD,
                    "歌手": NPCRole.BARD,
                    "贵族": NPCRole.NOBLE,
                    "国王": NPCRole.NOBLE,
                    "王后": NPCRole.NOBLE,
                    "仆人": NPCRole.SERVANT,
                    "侍从": NPCRole.SERVANT,
                    "工匠": NPCRole.ARTISAN,
                    "铁匠": NPCRole.ARTISAN,
                    "小偷": NPCRole.THIEF,
                    "强盗": NPCRole.THIEF,
                }
                role = role_mapping.get(role_hint)
            
            # 生成NPC
            npc = self.npc_generator.generate_npc(role=role, location=location, gender="random")
            
            # 创建智能体
            from tkg_models import CharacterAttributes, CombatPower
            from agent_system import CharacterAgent
            
            attributes = CharacterAttributes(
                description=npc.description,
                combat_power=CombatPower.MEDIUM,
                traits=npc.personality,
                background=npc.background
            )
            
            # NPC使用全球客户端进行对话（如果API key已配置）
            npc_agent = CharacterAgent(
                name=npc.name,
                attributes=attributes,
                relations=[],
                client=self.client,  # NPC可以使用LLM进行对话
                memory_system=self.client is not None and self.agent_system.memory_system or None,  # 有LLM才使用记忆系统
                emotion_system=self.emotion_system,
                motivation_system=self.motivation_system
            )
            
            # 设置NPC的location和goals
            npc_agent.location = npc.location
            npc_agent.goals = npc.goals
            
            # 初始化NPC的情感
            if self.emotion_system:
                self.emotion_system.set_emotion(npc.name, EmotionType.HAPPY, intensity=0.3, cause="初次登场")
            
            # 初始化NPC的动机
            if self.motivation_system and npc.goals:
                from motivation_system import Motivation, MotivationLevel, MotivationPriority, MotivationStatus
                for goal in npc.goals:
                    self.motivation_system.add_motivation(
                        npc.name,
                        Motivation(
                            description=goal,
                            level=MotivationLevel.MEDIUM_TERM,
                            priority=MotivationPriority.NORMAL,
                            status=MotivationStatus.IN_PROGRESS,
                            progress=0.1
                        )
                    )
            
            # 添加到智能体系统
            self.agent_system.agents[npc.name] = npc_agent
            
            print(f"✅ 自动生成NPC: {npc.name} ({npc.role}) 在 {npc.location}")
            return npc.name
            
        except Exception as e:
            print(f"❌ 自动生成NPC失败: {e}")
            return None

