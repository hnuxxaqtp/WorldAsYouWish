#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
长期记忆系统 - 基于向量检索的记忆管理
"""

import json
import os
from typing import List, Dict, Optional, Any
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer


class Memory:
    """单条记忆"""
    
    def __init__(
        self,
        character_name: str,
        content: str,
        memory_type: str,  # "dialogue", "event", "action", "observation"
        timestamp: Optional[str] = None,
        metadata: Optional[Dict] = None,
        embedding: Optional[np.ndarray] = None
    ):
        self.character_name = character_name
        self.content = content
        self.memory_type = memory_type
        self.timestamp = timestamp or datetime.now().isoformat()
        self.metadata = metadata or {}
        self.embedding = embedding
    
    def to_dict(self) -> Dict:
        """转换为字典（用于存储）"""
        return {
            "character_name": self.character_name,
            "content": self.content,
            "memory_type": self.memory_type,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "embedding": self.embedding.tolist() if self.embedding is not None else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Memory':
        """从字典创建"""
        if data.get("embedding"):
            data["embedding"] = np.array(data["embedding"])
        return cls(**{k: v for k, v in data.items() if k != 'embedding' or v is not None})


class MemorySystem:
    """角色记忆系统"""
    
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2", storage_dir: str = "memory_storage", model_dir: str = None):
        """
        初始化记忆系统
        
        Args:
            model_name: sentence-transformers 模型名称，默认使用支持多语言的模型
            storage_dir: 记忆存储目录
            model_dir: 模型存储目录（None表示使用项目根目录下的model文件夹）
        """
        self.model_name = model_name
        self.storage_dir = storage_dir
        self.model = None
        self.memories: Dict[str, List[Memory]] = {}  # character_name -> List[Memory]
        
        # 设置模型目录：优先使用传入的model_dir，否则使用项目根目录下的model文件夹
        if model_dir:
            self.model_dir = model_dir
        else:
            # 获取项目根目录
            # backend文件的路径：backend/memory_system.py
            # model目录在：model/
            # 需要从backend的父目录（project根目录）跳到model目录
            backend_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(backend_dir)
            self.model_dir = os.path.join(parent_dir, "model")
        
        # 确保存储目录存在
        os.makedirs(storage_dir, exist_ok=True)
    
    def _get_model_path(self) -> str:
        """获取模型存储路径"""
        # 直接使用 model_name 作为目录名，不进行转换
        model_path = os.path.join(self.model_dir, self.model_name)
        return model_path
    
    def _load_model(self):
        """延迟加载模型（强制使用本地缓存，不访问网络）"""
        if self.model is None:
            model_path = self._get_model_path()
            print(f"正在从本地加载记忆模型: {self.model_name}")
            print(f"  模型路径: {model_path}")
            
            # 检查模型目录是否存在
            if not os.path.exists(model_path):
                print(f"❌ 错误：模型目录不存在")
                print(f"提示：请先下载模型到指定目录")
                print(f"  方式1: 使用以下命令下载模型到本地")
                print(f"         python -c \"from sentence_transformers import SentenceTransformer; m=SentenceTransformer('{self.model_name}'); m.save('{model_path}')\"")
                print(f"  方式2: 手动从 huggingface 下载模型文件到以下目录:")
                print(f"         {model_path}")
                print(f"  或者运行项目根目录的下载脚本: python download_model.py")
                raise FileNotFoundError(f"模型目录不存在: {model_path}")
            
            # 检查模型文件是否完整
            config_file = os.path.join(model_path, "config_sentence_transformers.json")
            if not os.path.exists(config_file):
                print(f"❌ 错误：模型文件不完整，缺少 config_sentence_transformers.json")
                raise FileNotFoundError(f"模型文件不完整: {model_path}")
            
            try:
                # 直接从指定路径加载模型
                print(f"  正在加载模型文件...")
                self.model = SentenceTransformer(model_path)
                print(f"✅ 记忆模型加载完成（离线模式，路径: {model_path}）")
                return
            except Exception as e:
                print(f"❌ 模型加载失败: {e}")
                print(f"请检查模型文件是否完整")
                raise
    
    def _get_default_cache_dir(self) -> str:
        """获取默认的 sentence-transformers 缓存目录（用于提示信息）"""
        if os.name == 'nt':
            return os.path.join(os.environ.get('USERPROFILE', ''), '.cache', 'torch', 'sentence_transformers')
        else:
            return os.path.join(os.path.expanduser('~'), '.cache', 'torch', 'sentence_transformers')
    
    def add_memory(
        self,
        character_name: str,
        content: str,
        memory_type: str,
        metadata: Optional[Dict] = None,
        auto_save: bool = True
    ) -> Memory:
        """
        添加一条记忆
        
        Args:
            character_name: 角色名称
            content: 记忆内容
            memory_type: 记忆类型 (dialogue/event/action/observation)
            metadata: 额外元数据（如对话对象、事件参与者等）
            auto_save: 是否自动保存到磁盘，默认为True
        
        Returns:
            创建的记忆对象
        """
        # 延迟加载模型
        self._load_model()
        
        # 生成向量嵌入
        embedding = self.model.encode(content, convert_to_numpy=True)
        
        # 创建记忆
        memory = Memory(
            character_name=character_name,
            content=content,
            memory_type=memory_type,
            metadata=metadata,
            embedding=embedding
        )
        
        # 添加到记忆列表
        if character_name not in self.memories:
            self.memories[character_name] = []
        self.memories[character_name].append(memory)
        
        # 自动保存到磁盘
        if auto_save:
            self._save_single_character(character_name)
        
        return memory
    
    def _save_single_character(self, character_name: str):
        """
        保存单个角色的记忆到磁盘（用于自动保存）
        """
        if character_name not in self.memories:
            return
        
        character_dir = os.path.join(self.storage_dir, character_name)
        os.makedirs(character_dir, exist_ok=True)
        
        # 保存为JSONL格式
        file_path = os.path.join(character_dir, "memories.jsonl")
        with open(file_path, 'w', encoding='utf-8') as f:
            for memory in self.memories[character_name]:
                f.write(json.dumps(memory.to_dict(), ensure_ascii=False) + '\n')
    
    def retrieve_memories(
        self,
        character_name: str,
        query: str,
        top_k: int = 5,
        memory_types: Optional[List[str]] = None,
        min_similarity: float = 0.3
    ) -> List[Memory]:
        """
        检索相关记忆
        
        Args:
            character_name: 角色名称
            query: 查询文本
            top_k: 返回的最相关记忆数量
            memory_types: 过滤的记忆类型列表（None表示不过滤）
            min_similarity: 最小相似度阈值
        
        Returns:
            相关记忆列表，按相似度降序排序
        """
        # 延迟加载模型
        self._load_model()
        
        # 获取角色的所有记忆
        if character_name not in self.memories or not self.memories[character_name]:
            return []
        
        memories = self.memories[character_name]
        
        # 按类型过滤
        if memory_types:
            memories = [m for m in memories if m.memory_type in memory_types]
            if not memories:
                return []
        
        # 检查是否有嵌入
        memories_with_embedding = [m for m in memories if m.embedding is not None]
        if not memories_with_embedding:
            return []
        
        # 生成查询向量
        query_embedding = self.model.encode(query, convert_to_numpy=True)
        
        # 计算相似度（余弦相似度）
        similarities = []
        for memory in memories_with_embedding:
            # 余弦相似度
            sim = np.dot(query_embedding, memory.embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(memory.embedding) + 1e-9
            )
            similarities.append((sim, memory))
        
        # 排序并过滤
        similarities.sort(key=lambda x: x[0], reverse=True)
        filtered = [(s, m) for s, m in similarities if s >= min_similarity]
        
        # 返回top_k个
        return [memory for _, memory in filtered[:top_k]]
    
    def get_recent_memories(
        self,
        character_name: str,
        count: int = 10,
        memory_types: Optional[List[str]] = None
    ) -> List[Memory]:
        """
        获取最近的记忆
        
        Args:
            character_name: 角色名称
            count: 返回的记忆数量
            memory_types: 过滤的记忆类型列表
        
        Returns:
            最近的记忆列表，按时间降序排序
        """
        if character_name not in self.memories:
            return []
        
        memories = self.memories[character_name]
        
        # 按类型过滤
        if memory_types:
            memories = [m for m in memories if m.memory_type in memory_types]
        
        # 按时间排序
        memories.sort(key=lambda m: m.timestamp, reverse=True)
        
        return memories[:count]
    
    def get_all_memories(self, character_name: str) -> List[Memory]:
        """获取角色的所有记忆"""
        return self.memories.get(character_name, [])
    
    def format_memories_for_prompt(self, memories: List[Memory]) -> str:
        """
        将记忆格式化为适合LLM提示词的文本
        
        Args:
            memories: 记忆列表
        
        Returns:
            格式化的记忆文本
        """
        if not memories:
            return "无相关记忆"
        
        lines = []
        for i, memory in enumerate(memories, 1):
            type_emoji = {
                "dialogue": "💬",
                "event": "📅",
                "action": "⚡",
                "observation": "👁️"
            }.get(memory.memory_type, "📝")
            
            lines.append(f"{i}. {type_emoji} {memory.timestamp[:10]} - {memory.content}")
            if memory.metadata:
                for key, value in memory.metadata.items():
                    lines.append(f"   └ {key}: {value}")
        
        return "\n".join(lines)
    
    def save_to_disk(self):
        """将所有记忆保存到磁盘"""
        for character_name, memories in self.memories.items():
            character_dir = os.path.join(self.storage_dir, character_name)
            os.makedirs(character_dir, exist_ok=True)
            
            # 保存为JSONL格式
            file_path = os.path.join(character_dir, "memories.jsonl")
            with open(file_path, 'w', encoding='utf-8') as f:
                for memory in memories:
                    f.write(json.dumps(memory.to_dict(), ensure_ascii=False) + '\n')
        
        print(f"记忆已保存到 {self.storage_dir}")
    
    def load_from_disk(self):
        """从磁盘加载所有记忆"""
        if not os.path.exists(self.storage_dir):
            print(f"记忆存储目录不存在: {self.storage_dir}")
            return
        
        self.memories = {}
        
        for character_name in os.listdir(self.storage_dir):
            character_dir = os.path.join(self.storage_dir, character_name)
            if not os.path.isdir(character_dir):
                continue
            
            memories = []
            file_path = os.path.join(character_dir, "memories.jsonl")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            data = json.loads(line.strip())
                            memory = Memory.from_dict(data)
                            memories.append(memory)
                        except Exception as e:
                            print(f"加载记忆失败 ({character_name}): {e}")
            
            self.memories[character_name] = memories
        
        print(f"已从磁盘加载 {len(self.memories)} 个角色的记忆")
    
    def clear_memories(self, character_name: Optional[str] = None):
        """
        清除记忆
        
        Args:
            character_name: 角色名称，None表示清除所有记忆
        """
        if character_name:
            self.memories[character_name] = []
            print(f"已清除角色 {character_name} 的记忆")
        else:
            self.memories = {}
            print("已清除所有角色记忆")