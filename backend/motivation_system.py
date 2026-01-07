#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
角色动机系统 - 多层级动机模型
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import json


class MotivationLevel(Enum):
    """动机层级"""
    SHORT_TERM = "短期"      # 立即行动，几小时到几天内完成
    MEDIUM_TERM = "中期"     # 阶段计划，几周到几个月内完成
    LONG_TERM = "长期"      # 终极目标，可能贯穿整个故事


class MotivationPriority(Enum):
    """动机优先级"""
    CRITICAL = "紧急"       # 必须立即处理
    HIGH = "重要"          # 重要但可以稍后
    NORMAL = "一般"       # 正常优先级
    LOW = "较低"          # 可以推迟


class MotivationStatus(Enum):
    """动机状态"""
    PENDING = "待处理"     # 尚未开始
    IN_PROGRESS = "进行中"  # 正在执行
    PAUSED = "已暂停"      # 暂时搁置
    COMPLETED = "已完成"    # 已达成
    FAILED = "已失败"      # 无法达成
    ABANDONED = "已放弃"   # 主动放弃


class Motivation:
    """单个动机/目标"""
    
    def __init__(
        self,
        description: str,
        level: MotivationLevel,
        priority: MotivationPriority = MotivationPriority.NORMAL,
        status: MotivationStatus = MotivationStatus.PENDING,
        deadline: Optional[str] = None,
        progress: float = 0.0,
        sub_goals: Optional[List[str]] = None,
        blockers: Optional[List[str]] = None,
        prerequisites: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ):
        self.id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(description) % 10000}"
        self.description = description
        self.level = level
        self.priority = priority
        self.status = status
        self.deadline = deadline
        self.progress = progress  # 0.0 - 1.0
        self.sub_goals = sub_goals or []
        self.blockers = blockers or []  # 阻碍因素
        self.prerequisites = prerequisites or []  # 前置条件
        self.metadata = metadata or {}
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.completed_at: Optional[str] = None
        self.notes: List[str] = []  # 记录动机相关笔记
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "description": self.description,
            "level": self.level.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "deadline": self.deadline,
            "progress": self.progress,
            "sub_goals": self.sub_goals,
            "blockers": self.blockers,
            "prerequisites": self.prerequisites,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "notes": self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Motivation':
        """从字典创建"""
        motivation = cls(
            description=data.get("description", ""),
            level=MotivationLevel(data.get("level", MotivationLevel.SHORT_TERM.value)),
            priority=MotivationPriority(data.get("priority", MotivationPriority.NORMAL.value)),
            status=MotivationStatus(data.get("status", MotivationStatus.PENDING.value)),
            deadline=data.get("deadline"),
            progress=data.get("progress", 0.0),
            sub_goals=data.get("sub_goals", []),
            blockers=data.get("blockers", []),
            prerequisites=data.get("prerequisites", []),
            metadata=data.get("metadata", {})
        )
        motivation.id = data.get("id", motivation.id)
        motivation.created_at = data.get("created_at", motivation.created_at)
        motivation.updated_at = data.get("updated_at", motivation.updated_at)
        motivation.completed_at = data.get("completed_at")
        motivation.notes = data.get("notes", [])
        return motivation
    
    def update_progress(self, progress: float, note: Optional[str] = None):
        """更新进度"""
        self.progress = max(0.0, min(1.0, progress))
        self.updated_at = datetime.now().isoformat()
        
        if note:
            self.notes.append(f"[{datetime.now().strftime('%H:%M')}] {note}")
        
        # 如果达到100%，标记为完成
        if self.progress >= 1.0 and self.status != MotivationStatus.COMPLETED:
            self.status = MotivationStatus.COMPLETED
            self.completed_at = datetime.now().isoformat()
            self.notes.append("✅ 目标达成")
    
    def add_blocker(self, blocker: str):
        """添加阻碍因素"""
        if blocker not in self.blockers:
            self.blockers.append(blocker)
            self.updated_at = datetime.now().isoformat()
    
    def remove_blocker(self, blocker: str):
        """移除阻碍因素"""
        if blocker in self.blockers:
            self.blockers.remove(blocker)
            self.updated_at = datetime.now().isoformat()
    
    def set_status(self, status: MotivationStatus, note: Optional[str] = None):
        """设置状态"""
        old_status = self.status
        self.status = status
        self.updated_at = datetime.now().isoformat()
        
        if status == MotivationStatus.COMPLETED and not self.completed_at:
            self.completed_at = datetime.now().isoformat()
            self.progress = 1.0
        
        if note:
            self.notes.append(f"{old_status.value} → {status.value}: {note}")


class MotivationSystem:
    """动机系统管理器"""
    
    def __init__(self):
        self.motivations: Dict[str, List[Motivation]] = {}  # character_name -> List[Motivation]
        self.motivation_relationships: Dict[str, Dict[str, List[str]]] = {}  # 层级关系：依赖关系
    
    def initialize_character(self, character_name: str):
        """初始化角色动机系统"""
        if character_name not in self.motivations:
            self.motivations[character_name] = []
            self.motivation_relationships[character_name] = {
                "dependencies": {},  # motivation_id -> [dependent_ids]
                "blocks": {}        # motivation_id -> [blocked_ids]
            }
    
    def add_motivation(
        self,
        character_name: str,
        motivation: Motivation,
        depending_on: Optional[str] = None
    ) -> str:
        """
        添加动机
        
        Args:
            character_name: 角色名称
            motivation: 动机对象
            depending_on: 依赖的其他动机ID（完成另一个动机后才能开始）
        
        Returns:
            动机ID
        """
        self.initialize_character(character_name)
        
        # 添加动机
        self.motivations[character_name].append(motivation)
        
        # 建立依赖关系
        if depending_on:
            self._add_dependency(character_name, depending_on, motivation.id)
        
        return motivation.id
    
    def get_motivation(self, character_name: str, motivation_id: str) -> Optional[Motivation]:
        """获取特定动机"""
        if character_name not in self.motivations:
            return None
        
        for motivation in self.motivations[character_name]:
            if motivation.id == motivation_id:
                return motivation
        return None
    
    def get_motivations_by_level(
        self,
        character_name: str,
        level: MotivationLevel,
        status: Optional[MotivationStatus] = None
    ) -> List[Motivation]:
        """按层级获取动机"""
        if character_name not in self.motivations:
            return []
        
        motivations = [m for m in self.motivations[character_name] if m.level == level]
        
        if status:
            motivations = [m for m in motivations if m.status == status]
        
        return motivations
    
    def get_active_motivations(
        self,
        character_name: str,
        include_blocked: bool = False
    ) -> List[Motivation]:
        """
        获取所有活跃动机（待处理或进行中）
        
        Args:
            character_name: 角色名称
            include_blocked: 是否包含被阻碍的动机
        
        Returns:
            活跃动机列表
        """
        if character_name not in self.motivations:
            return []
        
        active = [
            m for m in self.motivations[character_name]
            if m.status in [MotivationStatus.PENDING, MotivationStatus.IN_PROGRESS]
        ]
        
        # 过滤掉被阻碍的动机
        if not include_blocked:
            active = [m for m in active if not self._is_blocked(character_name, m.id)]
        
        # 过滤掉未满足前置条件的
        active = [m for m in active if self._check_prerequisites(character_name, m)]
        
        return sorted(active, key=lambda m: (
            self._priority_score(m.priority),
            self._level_score(m.level)
        ))
    
    def _priority_score(self, priority: MotivationPriority) -> int:
        """优先级分数（越小越高）"""
        scores = {
            MotivationPriority.CRITICAL: 0,
            MotivationPriority.HIGH: 1,
            MotivationPriority.NORMAL: 2,
            MotivationPriority.LOW: 3
        }
        return scores.get(priority, 2)
    
    def _level_score(self, level: MotivationLevel) -> int:
        """层级分数（短期优先，数值越小）"""
        scores = {
            MotivationLevel.SHORT_TERM: 0,
            MotivationLevel.MEDIUM_TERM: 1,
            MotivationLevel.LONG_TERM: 2
        }
        return scores.get(level, 1)
    
    def _is_blocked(self, character_name: str, motivation_id: str) -> bool:
        """检查动机是否被阻碍"""
        if character_name not in self.motivation_relationships:
            return False
        
        blocked_by = self.motivation_relationships[character_name]["blocks"].get(motivation_id, [])
        return len(blocked_by) > 0
    
    def _check_prerequisites(self, character_name: str, motivation: Motivation) -> bool:
        """检查前置条件是否满足"""
        if not motivation.prerequisites:
            return True
        
        # 检查每个前置动机是否已完成
        for prereq_id in motivation.prerequisites:
            prereq = self.get_motivation(character_name, prereq_id)
            if not prereq or prereq.status != MotivationStatus.COMPLETED:
                return False
        
        return True
    
    def _add_dependency(self, character_name: str, parent_id: str, child_id: str):
        """添加依赖关系"""
        self.initialize_character(character_name)
        
        if parent_id not in self.motivation_relationships[character_name]["dependencies"]:
            self.motivation_relationships[character_name]["dependencies"][parent_id] = []
        self.motivation_relationships[character_name]["dependencies"][parent_id].append(child_id)
        
        if child_id not in self.motivation_relationships[character_name]["blocks"]:
            self.motivation_relationships[character_name]["blocks"][child_id] = []
        self.motivation_relationships[character_name]["blocks"][child_id].append(parent_id)
    
    def update_progress(
        self,
        character_name: str,
        motivation_id: str,
        progress: float,
        note: Optional[str] = None
    ) -> bool:
        """更新动机进度"""
        motivation = self.get_motivation(character_name, motivation_id)
        if not motivation:
            return False
        
        motivation.update_progress(progress, note)
        
        # 检查是否有依赖此动机的其他动机
        if character_name in self.motivation_relationships:
            dependents = self.motivation_relationships[character_name]["dependencies"].get(motivation_id, [])
            for dep_id in dependents:
                dep_motivation = self.get_motivation(character_name, dep_id)
                if dep_motivation and motivation.status == MotivationStatus.COMPLETED:
                    # 前置已完成，可以开始了
                    if dep_motivation.status == MotivationStatus.PENDING:
                        dep_motivation.set_status(MotivationStatus.IN_PROGRESS, "前置目标已达成")
        
        return True
    
    def set_status(
        self,
        character_name: str,
        motivation_id: str,
        status: MotivationStatus,
        note: Optional[str] = None
    ) -> bool:
        """设置动机状态"""
        motivation = self.get_motivation(character_name, motivation_id)
        if not motivation:
            return False
        
        motivation.set_status(status, note)
        return True
    
    def add_blocker(self, character_name: str, motivation_id: str, blocker: str) -> bool:
        """添加阻碍因素"""
        motivation = self.get_motivation(character_name, motivation_id)
        if not motivation:
            return False
        
        motivation.add_blocker(blocker)
        return True
    
    def complete_motivation(self, character_name: str, motivation_id: str, note: Optional[str] = None) -> bool:
        """完成动机"""
        motivation = self.get_motivation(character_name, motivation_id)
        if not motivation:
            return False
        
        motivation.update_progress(1.0, note or "目标达成")
        
        # 激活依赖此动机的其他动机
        if character_name in self.motivation_relationships:
            dependents = self.motivation_relationships[character_name]["dependencies"].get(motivation_id, [])
            for dep_id in dependents:
                dep_motivation = self.get_motivation(character_name, dep_id)
                if dep_motivation and dep_motivation.status == MotivationStatus.PENDING:
                    dep_motivation.set_status(MotivationStatus.IN_PROGRESS, "前置目标已达成")
        
        return True
    
    def abandon_motivation(self, character_name: str, motivation_id: str, reason: Optional[str] = None) -> bool:
        """放弃动机"""
        motivation = self.get_motivation(character_name, motivation_id)
        if not motivation:
            return False
        
        motivation.set_status(MotivationStatus.ABANDONED, reason or "主动放弃")
        return True
    
    def get_motivation_summary(self, character_name: str) -> Dict:
        """获取动机汇总"""
        if character_name not in self.motivations:
            return {
                "total": 0,
                "by_level": {
                    MotivationLevel.SHORT_TERM.value: 0,
                    MotivationLevel.MEDIUM_TERM.value: 0,
                    MotivationLevel.LONG_TERM.value: 0
                },
                "by_status": {},
                "active_motivations": []
            }
        
        motivations = self.motivations[character_name]
        
        # 按层级统计
        by_level = {
            MotivationLevel.SHORT_TERM.value: len([m for m in motivations if m.level == MotivationLevel.SHORT_TERM]),
            MotivationLevel.MEDIUM_TERM.value: len([m for m in motivations if m.level == MotivationLevel.MEDIUM_TERM]),
            MotivationLevel.LONG_TERM.value: len([m for m in motivations if m.level == MotivationLevel.LONG_TERM])
        }
        
        # 按状态统计
        by_status = {}
        for status in MotivationStatus:
            count = len([m for m in motivations if m.status == status])
            by_status[status.value] = count
        
        # 获取活跃动机
        active = self.get_active_motivations(character_name)
        
        return {
            "total": len(motivations),
            "by_level": by_level,
            "by_status": by_status,
            "active_motivations": [m.to_dict() for m in active[:5]],  # 前5个活跃动机
            "completion_rate": len([m for m in motivations if m.status == MotivationStatus.COMPLETED]) / len(motivations) if motivations else 0.0
        }
    
    def format_for_planning(self, character_name: str) -> str:
        """格式化用于规划的动机信息"""
        summary = self.get_motivation_summary(character_name)
        
        if summary["total"] == 0:
            return "当前无明确动机"
        
        lines = []
        
        # 短期目标
        short = self.get_motivations_by_level(character_name, MotivationLevel.SHORT_TERM)
        if short:
            lines.append("【短期目标】")
            for m in self.get_active_motivations(character_name):
                if m.level == MotivationLevel.SHORT_TERM:
                    lines.append(f"  • {m.description} ({m.priority.value}, 进度: {m.progress*100:.0f}%)")
                    if m.blockers:
                        lines.append(f"    阻碍: {', '.join(m.blockers)}")
        
        # 中期目标
        medium = self.get_motivations_by_level(character_name, MotivationLevel.MEDIUM_TERM)
        if medium:
            lines.append("【中期目标】")
            for m in medium[:3]:  # 只显示前3个
                lines.append(f"  • {m.description} ({m.priority.value}, 进度: {m.progress*100:.0f}%)")
        
        # 长期目标
        long = self.get_motivations_by_level(character_name, MotivationLevel.LONG_TERM)
        if long:
            lines.append("【长期目标】")
            for m in long[:2]:  # 只显示前2个
                lines.append(f"  • {m.description} ({m.priority.value}, 进度: {m.progress*100:.0f}%)")
        
        lines.append(f"完成率: {summary['completion_rate']*100:.1f}%")
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "motivations": {
                char: [m.to_dict() for m in motivations]
                for char, motivations in self.motivations.items()
            },
            "relationships": self.motivation_relationships
        }