#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多智能体系统 - 每个角色是一个智能体
"""

from typing import Dict, List, Optional, Any
from openai import OpenAI
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tkg_models import CharacterAttributes, RelationsSnapshot
from memory_system import MemorySystem
from emotion_system import EmotionSystem
from motivation_system import MotivationSystem
import json


class CharacterAgent:
    """角色智能体"""
    
    def __init__(
        self,
        name: str,
        attributes: Optional[CharacterAttributes],
        relations: List[Dict],
        client: Optional[OpenAI],
        memory_system: Optional[MemorySystem] = None,
        emotion_system: Optional[EmotionSystem] = None,
        motivation_system: Optional[MotivationSystem] = None
    ):
        self.name = name
        self.attributes = attributes
        self.relations = relations
        self.client = client
        self.memory_system = memory_system
        self.emotion_system = emotion_system
        self.motivation_system = motivation_system
        
        # 动态状态
        self.location = "未知"
        self.status = "正常"
        self.goals: List[str] = []
        self.inventory: List[str] = []
        
        # 初始化情感状态
        if emotion_system:
            emotion_system.initialize_character(self.name)
        
        # 初始化动机系统
        if motivation_system:
            motivation_system.initialize_character(self.name)
        
    def get_character_prompt(self) -> str:
        """生成角色描述提示词"""
        prompt_parts = [f"角色名称: {self.name}"]
        
        if self.attributes:
            if self.attributes.traits:
                prompt_parts.append(f"性格特质: {', '.join(self.attributes.traits)}")
            if self.attributes.combat_power != "未知":
                prompt_parts.append(f"战斗力: {self.attributes.combat_power}")
            if self.attributes.inventory:
                prompt_parts.append(f"持有物品: {', '.join(self.attributes.inventory)}")
        
        if self.goals:
            prompt_parts.append(f"当前目标: {', '.join(self.goals)}")
        
        if self.location != "未知":
            prompt_parts.append(f"当前位置: {self.location}")
        
        # 添加情感状态
        if self.emotion_system:
            emotion_state = self.emotion_system.get_emotion_state(self.name)
            if emotion_state:
                prompt_parts.append(
                    f"当前情感: {emotion_state.primary_emotion.value} "
                    f"(强度: {emotion_state.intensity:.2f})"
                )
        
        if self.relations:
            prompt_parts.append("关系网络:")
            for rel in self.relations[:5]:  # 只显示前5个关系
                target = rel.get("target", "")
                rel_type = rel.get("type", "")
                score = rel.get("score", 0.0)
                prompt_parts.append(f"  - 与 {target}: {rel_type} (强度: {score:.2f})")
        
        return "\n".join(prompt_parts)
    
    async def generate_plan(self, world_context: Dict) -> Dict:
        """生成角色计划"""
        if not self.client:
            return {
                "plan": "继续当前行动",
                "steps": [],
                "reasoning": "无LLM支持"
            }
        
        character_desc = self.get_character_prompt()
        
        # 检索相关记忆
        memory_text = "无相关记忆"
        if self.memory_system:
            relevant_memories = self.memory_system.retrieve_memories(
                character_name=self.name,
                query=f"当前目标: {' '.join(self.goals)}",
                top_k=5
            )
            memory_text = self.memory_system.format_memories_for_prompt(relevant_memories)
        
        # 获取动机信息
        motivation_text = "当前无明确动机"
        if self.motivation_system:
            motivation_text = self.motivation_system.format_for_planning(self.name)
        
        prompt = f"""你是一个故事中的角色智能体。根据角色设定、记忆、动机和当前世界状态，为角色制定一个合理的行动计划。

【角色信息】
{character_desc}

【角色记忆】（重要：这些是角色过去的重要经历，做决定时要考虑）
{memory_text}

【角色动机】（关键：这是角色的目标和驱动，所有行动都应服务于这些动机）
{motivation_text}

【世界状态】
{json.dumps(world_context, ensure_ascii=False, indent=2)}

【任务】
为 {self.name} 制定一个短期行动计划（3-5步），计划应该：
1. 优先完成紧急的短期目标
2. 推进中期的核心目标
3. 始终朝着长期目标前进
4. 符合角色的性格特质
5. 考虑角色与其他角色的关系
6. 参考角色记忆，保持行为一致性
7. 符合当前世界状态和条件限制

请以JSON格式输出：
{{
  "plan": "计划概述",
  "steps": ["步骤1", "步骤2", "步骤3"],
  "reasoning": "制定计划的理由（说明如何考虑了记忆和现状）",
  "expected_outcome": "预期结果"
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="Qwen/Qwen2.5-7B-Instruct",
                messages=[
                    {"role": "system", "content": "你是角色智能体，负责制定符合角色设定的行动计划。只输出JSON，不要其他文字。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            return {
                "plan": "继续当前行动",
                "steps": [],
                "reasoning": f"计划生成失败: {str(e)}"
            }
    
    async def generate_dialogue(
        self,
        listener: 'CharacterAgent',
        topic: Optional[str] = None,
        context: Optional[str] = None
    ) -> Dict:
        """生成对话"""
        if not self.client:
            return {
                "speaker": self.name,
                "listener": listener.name,
                "content": "（无LLM支持，无法生成对话）"
            }
        
        speaker_desc = self.get_character_prompt()
        listener_desc = listener.get_character_prompt()
        
        # 获取两个角色之间的关系
        relation_info = "无特殊关系"
        for rel in self.relations:
            if rel.get("target") == listener.name:
                relation_info = f"{rel.get('type', '')} (强度: {rel.get('score', 0.0):.2f})"
                break
        
        # 检索说话者关于倾听者的记忆
        speaker_memory_text = "无相关记忆"
        if self.memory_system:
            relevant_memories = self.memory_system.retrieve_memories(
                character_name=self.name,
                query=f"{listener.name} {topic if topic else '关系'}",
                top_k=3
            )
            speaker_memory_text = self.memory_system.format_memories_for_prompt(relevant_memories)
        
        # 获取情感影响描述
        emotion_influence = ""
        if self.emotion_system:
            emotion_influence = self.emotion_system.get_emotion_influence_on_dialogue(self.name)
        
        prompt = f"""你是一个故事中的角色智能体。根据角色设定、记忆、情感和关系，生成符合角色性格的对话。

【说话者信息】
{speaker_desc}

【说话者记忆】（关键：这影响说话者对倾听者的态度和说话内容）
{speaker_memory_text}

【说话者情感状态】（重要：需要根据情感调整说话语气和方式）
{emotion_influence if emotion_influence else "当前情绪平静"}

【倾听者信息】
{listener_desc}

【关系】
{self.name} 与 {listener.name} 的关系: {relation_info}

【对话主题】
{topic if topic else "日常交流"}

【上下文】
{context if context else "无特殊上下文"}

【任务】
生成 {self.name} 对 {listener.name} 说的一段话。对话应该：
1. 符合说话者的性格特质
2. 考虑双方的关系强度
3. 参考说话者的记忆，保持对话的一致性和连贯性
4. 根据说话者的情感状态调整语气和表达方式（这是关键！）
5. 符合对话主题和上下文
6. 自然流畅，符合故事风格

请以JSON格式输出：
{{
  "speaker": "{self.name}",
  "listener": "{listener.name}",
  "content": "对话内容",
  "tone": "对话语气（如：友好、紧张、愤怒等）",
  "intent": "对话意图"
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="Qwen/Qwen2.5-7B-Instruct",
                messages=[
                    {"role": "system", "content": "你是角色智能体，负责生成符合角色设定的对话。只输出JSON，不要其他文字。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            return {
                "speaker": self.name,
                "listener": listener.name,
                "content": f"（对话生成失败: {str(e)}）"
            }
    
    async def generate_action(
        self,
        action_type: str,
        target: Optional[str] = None,
        context: Optional[str] = None
    ) -> Dict:
        """生成角色行动"""
        if not self.client:
            return {
                "character": self.name,
                "action": action_type,
                "result": "（无LLM支持，无法生成行动）"
            }
        
        character_desc = self.get_character_prompt()
        
        prompt = f"""你是一个故事中的角色智能体。根据角色设定，生成符合角色性格的行动。

【角色信息】
{character_desc}

【行动类型】
{action_type}

【目标】
{target if target else "无特定目标"}

【上下文】
{context if context else "无特殊上下文"}

【任务】
生成 {self.name} 执行 {action_type} 的行动描述。行动应该：
1. 符合角色的性格特质
2. 考虑角色的能力和物品
3. 符合当前世界状态
4. 具有合理的结果

请以JSON格式输出：
{{
  "character": "{self.name}",
  "action": "{action_type}",
  "description": "行动描述",
  "result": "行动结果",
  "consequences": ["后果1", "后果2"]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="Qwen/Qwen2.5-7B-Instruct",
                messages=[
                    {"role": "system", "content": "你是角色智能体，负责生成符合角色设定的行动。只输出JSON，不要其他文字。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            return {
                "character": self.name,
                "action": action_type,
                "result": f"（行动生成失败: {str(e)}）"
            }


class AgentSystem:
    """智能体系统管理器"""
    
    def __init__(
        self,
        client: Optional[OpenAI],
        memory_system: Optional[MemorySystem] = None,
        emotion_system: Optional[EmotionSystem] = None,
        motivation_system: Optional[MotivationSystem] = None
    ):
        self.client = client
        self.memory_system = memory_system
        self.emotion_system = emotion_system
        self.motivation_system = motivation_system
        self.agents: Dict[str, CharacterAgent] = {}
    
    def initialize_agents(self, world_data: Dict):
        """从世界数据初始化智能体（保留已存在的NPC）"""
        # 加载角色数据
        characters_data = world_data.get("characters", {})
        relations_data = world_data.get("relations", {})
        
        # 为每个角色创建或更新智能体
        for char_name, char_attrs in characters_data.items():
            # 如果角色已存在（比如是手动添加的NPC），跳过它
            if char_name in self.agents:
                continue
            
            # 获取该角色的关系
            char_relations = []
            for edge in relations_data.get("edges", []):
                if edge.get("a") == char_name:
                    char_relations.append({
                        "target": edge.get("b"),
                        "type": edge.get("type"),
                        "score": edge.get("score", 0.0)
                    })
            
            # 创建智能体
            agent = CharacterAgent(
                name=char_name,
                attributes=char_attrs,
                relations=char_relations,
                client=self.client,
                memory_system=self.memory_system,
                emotion_system=self.emotion_system,
                motivation_system=self.motivation_system
            )
            
            # 设置初始状态
            if "goals" in world_data:
                agent.goals = world_data["goals"].get(char_name, [])
            if "locations" in world_data:
                agent.location = world_data["locations"].get(char_name, "未知")
            
            self.agents[char_name] = agent
        
        # 计算：基础角色数 + 动态添加的NPC数
        base_chars = len(characters_data)
        total_agents = len(self.agents)
        dynamic_npcs = total_agents - base_chars
        
        if dynamic_npcs > 0:
            print(f"✅ 已初始化 {base_chars} 个基础角色 + {dynamic_npcs} 个动态NPC = 共 {total_agents} 个智能体")
        else:
            print(f"✅ 已初始化 {len(self.agents)} 个角色智能体")
    
    def get_agent(self, name: str) -> Optional[CharacterAgent]:
        """获取智能体"""
        return self.agents.get(name)
    
    def get_all_agents(self) -> List[CharacterAgent]:
        """获取所有智能体"""
        return list(self.agents.values())

