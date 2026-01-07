#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
角色情感系统 - 动态情感模型
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum
import json


class EmotionType(Enum):
    """基本情感类型"""
    HAPPY = "快乐"
    SAD = "悲伤"
    ANGRY = "愤怒"
    FEAR = "恐惧"
    SURPRISE = "惊讶"
    DISGUST = "厌恶"
    NEUTRAL = "平静"
    ANXIOUS = "焦虑"
    CONFIDENT = "自信"
    TIRED = "疲惫"


class EmotionState:
    """角色情感状态"""
    
    def __init__(
        self,
        primary_emotion: EmotionType = EmotionType.NEUTRAL,
        intensity: float = 0.5,  # 0.0 - 1.0, 情感强度
        secondary_emotion: Optional[EmotionType] = None,
        secondary_intensity: float = 0.3
    ):
        self.primary_emotion = primary_emotion
        self.intensity = intensity
        self.secondary_emotion = secondary_emotion or EmotionType.NEUTRAL
        self.secondary_intensity = secondary_intensity
        self.last_updated = datetime.now().isoformat()
        self.history: List[Dict] = []  # 情感变化历史
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "primary_emotion": self.primary_emotion.value,
            "intensity": self.intensity,
            "secondary_emotion": self.secondary_emotion.value,
            "secondary_intensity": self.secondary_intensity,
            "last_updated": self.last_updated,
            "history": self.history[-10:]  # 只保留最近10条历史
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EmotionState':
        """从字典创建"""
        primary = EmotionType(data.get("primary_emotion", EmotionType.NEUTRAL.value))
        secondary = EmotionType(data.get("secondary_emotion", EmotionType.NEUTRAL.value))
        
        state = cls(
            primary_emotion=primary,
            intensity=data.get("intensity", 0.5),
            secondary_emotion=secondary,
            secondary_intensity=data.get("secondary_intensity", 0.3)
        )
        state.last_updated = data.get("last_updated", datetime.now().isoformat())
        state.history = data.get("history", [])
        return state
    
    def add_history(self, emotion: EmotionType, intensity: float, cause: str):
        """添加情感变化历史"""
        self.history.append({
            "emotion": emotion.value,
            "intensity": intensity,
            "cause": cause,
            "timestamp": datetime.now().isoformat()
        })
        # 只保留最近20条
        if len(self.history) > 20:
            self.history = self.history[-20:]


class EmotionTrigger:
    """情感触发器"""
    
    def __init__(
        self,
        trigger_type: str,  # "dialogue", "event", "action", "observation"
        keywords: List[str],  # 触发关键词
        target_emotion: EmotionType,
        intensity_change: float,  # 强度变化（-1.0 到 1.0）
        decay_rate: float = 0.1  # 衰减率
    ):
        self.trigger_type = trigger_type
        self.keywords = keywords
        self.target_emotion = target_emotion
        self.intensity_change = intensity_change
        self.decay_rate = decay_rate
        self.min_intensity = 0.0
        self.max_intensity = 1.0


class EmotionSystem:
    """情感系统管理器"""
    
    def __init__(self):
        self.emotion_states: Dict[str, EmotionState] = {}  # character_name -> EmotionState
        self.triggers = self._default_triggers()
    
    def _default_triggers(self) -> List[EmotionTrigger]:
        """默认情感触发器"""
        triggers = [
            # 正向情感
            EmotionTrigger("dialogue", ["感谢", "谢谢", "高兴", "开心", "喜欢", "爱", "赞美"], 
                         EmotionType.HAPPY, 0.3),
            EmotionTrigger("dialogue", ["成功", "胜利", "赢了", "做到", "完成"], 
                         EmotionType.CONFIDENT, 0.25),
            EmotionTrigger("event", ["胜利", "成功", "庆典", "奖励"], 
                         EmotionType.HAPPY, 0.35),
            
            # 负向情感
            EmotionTrigger("dialogue", ["讨厌", "恨", "愤怒", "生气", "滚", "去死"], 
                         EmotionType.ANGRY, 0.4),
            EmotionTrigger("dialogue", ["害怕", "恐惧", "担心", "担忧", "危险"], 
                         EmotionType.FEAR, 0.3),
            EmotionTrigger("dialogue", ["难过", "悲伤", "伤心", "哭", "痛苦"], 
                         EmotionType.SAD, 0.35),
            EmotionTrigger("event", ["失败", "死亡", "损失", "伤害"], 
                         EmotionType.SAD, 0.4),
            EmotionTrigger("event", ["攻击", "威胁", "危险"], 
                         EmotionType.FEAR, 0.35),
            
            # 其他情感
            EmotionTrigger("dialogue", ["惊讶", "意外", "不敢相信", "怎么可能"], 
                         EmotionType.SURPRISE, 0.3),
            EmotionTrigger("dialogue", ["恶心", "厌恶", "受不了"], 
                         EmotionType.DISGUST, 0.35),
            EmotionTrigger("dialogue", ["焦虑", "紧张", "不安", "担心"], 
                         EmotionType.ANXIOUS, 0.3),
            EmotionTrigger("event", ["意外", "突然", "突变"], 
                         EmotionType.SURPRISE, 0.4),
            EmotionTrigger("dialogue", ["累", "疲惫", "休息", "困"], 
                         EmotionType.TIRED, 0.25),
            EmotionTrigger("event", ["战斗", "劳动", "长途"], 
                         EmotionType.TIRED, 0.2),
            
            # 关系相关
            EmotionTrigger("dialogue", ["背叛", "欺骗", "谎言"], 
                         EmotionType.ANGRY, 0.45),
            EmotionTrigger("dialogue", ["信任", "相信", "支持"], 
                         EmotionType.CONFIDENT, 0.3),
        ]
        return triggers
    
    def initialize_character(self, character_name: str) -> EmotionState:
        """初始化角色情感状态"""
        if character_name not in self.emotion_states:
            self.emotion_states[character_name] = EmotionState()
        return self.emotion_states[character_name]
    
    def get_emotion_state(self, character_name: str) -> Optional[EmotionState]:
        """获取角色情感状态"""
        return self.emotion_states.get(character_name)
    
    def process_trigger(
        self, 
        character_name: str, 
        trigger_type: str, 
        content: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        处理情感触发，更新角色情感状态
        
        Args:
            character_name: 角色名称
            trigger_type: 触发类型 (dialogue/event/action/observation)
            content: 触发内容
            metadata: 额外的元数据
        
        Returns:
            情感变化信息
        """
        # 初始化（如果需要）
        if character_name not in self.emotion_states:
            self.initialize_character(character_name)
        
        state = self.emotion_states[character_name]
        
        # 检查触发器
        matched_triggers = []
        for trigger in self.triggers:
            if trigger.trigger_type != trigger_type:
                continue
            
            # 检查关键词匹配
            for keyword in trigger.keywords:
                if keyword in content:
                    matched_triggers.append(trigger)
                    break
        
        if not matched_triggers:
            return {
                "changed": False,
                "message": "没有匹配的情感触发器"
            }
        
        # 应用最强的触发器
        best_trigger = max(matched_triggers, key=lambda t: abs(t.intensity_change))
        
        # 计算新的情感强度
        old_emotion = state.primary_emotion
        old_intensity = state.intensity
        
        # 如果是同一个情感，累加强度
        if state.primary_emotion == best_trigger.target_emotion:
            state.intensity += best_trigger.intensity_change
        else:
            # 不同情感，逐渐过渡
            if abs(best_trigger.intensity_change) > state.intensity:
                state.primary_emotion = best_trigger.target_emotion
                state.intensity = abs(best_trigger.intensity_change)
        
        # 限制在 0.0 - 1.0 范围内
        state.intensity = max(best_trigger.min_intensity, 
                             min(best_trigger.max_intensity, state.intensity))
        
        # 更新时间
        state.last_updated = datetime.now().isoformat()
        
        # 添加历史记录
        cause_text = f"{trigger_type}: {content[:50]}"
        state.add_history(best_trigger.target_emotion, state.intensity, cause_text)
        
        return {
            "changed": True,
            "character_name": character_name,
            "old_emotion": old_emotion.value,
            "new_emotion": best_trigger.target_emotion.value,
            "old_intensity": old_intensity,
            "new_intensity": state.intensity,
            "trigger_cause": cause_text
        }
    
    def set_emotion(self, character_name: str, emotion: EmotionType, intensity: float = 0.5, cause: str = "手动设置") -> Dict:
        """
        直接设置角色的情感状态
        
        Args:
            character_name: 角色名称
            emotion: 要设置的情感类型
            intensity: 情感强度 (0.0 - 1.0)
            cause: 设置原因
        
        Returns:
            情感变化信息
        """
        # 初始化（如果需要）
        if character_name not in self.emotion_states:
            self.initialize_character(character_name)
        
        state = self.emotion_states[character_name]
        
        # 记录旧状态
        old_emotion = state.primary_emotion
        old_intensity = state.intensity
        
        # 设置新情感
        state.primary_emotion = emotion
        state.intensity = max(0.0, min(1.0, intensity))
        
        # 更新时间
        state.last_updated = datetime.now().isoformat()
        
        # 添加历史记录
        state.add_history(emotion, state.intensity, cause)
        
        return {
            "changed": True,
            "character_name": character_name,
            "old_emotion": old_emotion.value,
            "new_emotion": emotion.value,
            "old_intensity": old_intensity,
            "new_intensity": state.intensity,
            "cause": cause
        }
    
    def apply_emotion_decay(self, character_name: str, decay_factor: float = 0.1) -> Dict:
        """
        应用情感衰减，情感会逐渐回归中性状态
        
        Args:
            character_name: 角色名称
            decay_factor: 衰减因子
        
        Returns:
            衰减结果
        """
        if character_name not in self.emotion_states:
            return {"changed": False, "message": "角色不存在"}
        
        state = self.emotion_states[character_name]
        
        if state.primary_emotion == EmotionType.NEUTRAL:
            return {"changed": False, "message": "已经是中性状态"}
        
        old_intensity = state.intensity
        state.intensity *= (1.0 - decay_factor)
        
        # 如果强度太低，回归中性
        if state.intensity < 0.1:
            state.primary_emotion = EmotionType.NEUTRAL
            state.intensity = 0.5
        else:
            state.intensity = max(0.1, state.intensity)
        
        state.last_updated = datetime.now().isoformat()
        
        return {
            "changed": True,
            "character_name": character_name,
            "old_intensity": old_intensity,
            "new_intensity": state.intensity,
            "decayed_by": decay_factor
        }
    
    def get_emotion_influence_on_dialogue(self, character_name: str) -> str:
        """
        获取情感对对话的影响描述
        
        Returns:
            情感影响描述
        """
        state = self.emotion_states.get(character_name)
        if not state or state.primary_emotion == EmotionType.NEUTRAL:
            return ""
        
        emotion_map = {
            EmotionType.HAPPY: "语气轻松愉快，言辞积极",
            EmotionType.SAD: "语气低沉，言辞悲伤",
            EmotionType.ANGRY: "语气激动，可能带有攻击性",
            EmotionType.FEAR: "语气紧张，显得担忧",
            EmotionType.SURPRISE: "语气惊讶，带有好奇或困惑",
            EmotionType.DISGUST: "语气厌恶，可能表达不满",
            EmotionType.ANXIOUS: "语气焦虑，显得急躁",
            EmotionType.CONFIDENT: "语气坚定，充满信心",
            EmotionType.TIRED: "语气疲惫，反应迟缓"
        }
        
        intensity_desc = ""
        if state.intensity > 0.7:
            intensity_desc = "情感非常强烈，明显影响说话方式"
        elif state.intensity > 0.4:
            intensity_desc = "情感较为明显，轻微影响说话方式"
        else:
            intensity_desc = "情感较为微弱，对说话方式影响较小"
        
        base = emotion_map.get(state.primary_emotion, "")
        return f"{base}，{intensity_desc}。" if base else ""
    
    def add_custom_trigger(
        self,
        trigger_type: str,
        keywords: List[str],
        target_emotion: str,
        intensity_change: float,
        decay_rate: float = 0.1
    ):
        """添加自定义情感触发器"""
        try:
            emotion = EmotionType(target_emotion)
            trigger = EmotionTrigger(
                trigger_type=trigger_type,
                keywords=keywords,
                target_emotion=emotion,
                intensity_change=intensity_change,
                decay_rate=decay_rate
            )
            self.triggers.append(trigger)
            return True
        except ValueError:
            return False
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "emotion_states": {
                name: state.to_dict()
                for name, state in self.emotion_states.items()
            },
            "triggers_count": len(self.triggers)
        }