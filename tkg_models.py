#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum

class TKGEntry(BaseModel):
    """TKG四元组条目"""
    tau: str = Field(..., description="时间戳，格式：ch{chapter_id}_e{idx}")
    h: str = Field(..., description="头实体")
    r: str = Field(..., description="关系")
    t: str = Field(..., description="尾实体或概念")
    meta: Dict[str, Any] = Field(default_factory=dict, description="元数据")

class CombatPower(str, Enum):
    """战斗力等级"""
    WEAK = "弱"
    MEDIUM = "中"
    STRONG = "强"
    UNKNOWN = "未知"

class CharacterAttributes(BaseModel):
    """角色属性"""
    combat_power: CombatPower = Field(default=CombatPower.UNKNOWN, description="战斗力")
    inventory: List[str] = Field(default_factory=list, description="物品清单")
    traits: List[str] = Field(default_factory=list, description="性格特质")

class RelationEdge(BaseModel):
    """关系边"""
    a: str = Field(..., description="起始节点")
    b: str = Field(..., description="目标节点")
    type: str = Field(..., description="关系类型")
    score: float = Field(..., ge=0.0, le=1.0, description="关系强度")
    evidence: str = Field(default="", description="关系证据")

class CharactersSnapshot(BaseModel):
    """角色属性快照"""
    chapter_id: int = Field(..., description="章节ID")
    characters: Dict[str, CharacterAttributes] = Field(default_factory=dict, description="角色属性表")

class RelationsSnapshot(BaseModel):
    """关系图快照"""
    chapter_id: int = Field(..., description="章节ID")
    nodes: List[str] = Field(default_factory=list, description="节点列表")
    edges: List[RelationEdge] = Field(default_factory=list, description="边列表")

class TKGChapter(BaseModel):
    """章节TKG"""
    chapter_id: int = Field(..., description="章节ID")
    triples: List[TKGEntry] = Field(default_factory=list, description="四元组列表")

class EventFeasibility(BaseModel):
    """事件可行性判定结果"""
    ok: bool = Field(..., description="是否可行")
    score: float = Field(..., ge=0.0, le=1.0, description="可行性评分")
    reasons: List[str] = Field(default_factory=list, description="判定理由")
