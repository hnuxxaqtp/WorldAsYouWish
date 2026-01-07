#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
世界管理器 - 管理多个独立的游戏世界
"""

import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class World:
    """世界数据模型"""
    
    def __init__(
        self,
        world_id: str,
        name: str,
        description: str = "",
        creation_time: Optional[str] = None,
        last_modified: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        self.world_id = world_id
        self.name = name
        self.description = description
        self.creation_time = creation_time or datetime.now().isoformat()
        self.last_modified = last_modified or datetime.now().isoformat()
        self.metadata = metadata or {"locations": [], "characters": {}, "relations": {}}
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "world_id": self.world_id,
            "name": self.name,
            "description": self.description,
            "creation_time": self.creation_time,
            "last_modified": self.last_modified,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'World':
        """从字典创建World对象"""
        return cls(
            world_id=data["world_id"],
            name=data["name"],
            description=data.get("description", ""),
            creation_time=data.get("creation_time"),
            last_modified=data.get("last_modified"),
            metadata=data.get("metadata", {})
        )


class WorldManager:
    """世界管理器 - 负责世界的CRUD操作"""
    
    def __init__(self, storage_dir: str = None):
        """初始化世界管理器"""
        if storage_dir is None:
            # 默认存储在项目根目录下的worlds文件夹
            self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            storage_dir = os.path.join(self.base_dir, "worlds")
        
        self.storage_dir = Path(storage_dir)
        self.worlds_file = self.storage_dir / "worlds.json"
        self.worlds_dir = self.storage_dir / "world_data"
        
        # 创建必要的目录
        self.storage_dir.mkdir(exist_ok=True)
        self.worlds_dir.mkdir(exist_ok=True)
        
        # 加载世界列表
        self._worlds: Dict[str, World] = {}
        self._load_worlds_list()
    
    def _load_worlds_list(self):
        """加载世界列表"""
        if self.worlds_file.exists():
            try:
                with open(self.worlds_file, 'r', encoding='utf-8') as f:
                    worlds_data = json.load(f)
                    for world_data in worlds_data:
                        world = World.from_dict(world_data)
                        self._worlds[world.world_id] = world
            except Exception as e:
                print(f"⚠️ 加载世界列表失败: {e}")
                self._worlds = {}
    
    def _save_worlds_list(self):
        """保存世界列表"""
        try:
            worlds_list = [world.to_dict() for world in self._worlds.values()]
            with open(self.worlds_file, 'w', encoding='utf-8') as f:
                json.dump(worlds_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise Exception(f"保存世界列表失败: {e}")
    
    def _generate_world_id(self, name: str) -> str:
        """生成唯一的世界ID"""
        base_id = name.lower().replace(" ", "_").replace(" ", "").replace("/", "_")
        base_id = "".join(c for c in base_id if c.isalnum() or c == "_")
        
        # 如果ID冲突，添加数字后缀
        counter = 1
        world_id = base_id
        while world_id in self._worlds:
            world_id = f"{base_id}_{counter}"
            counter += 1
        
        return world_id
    
    def create_world(self, name: str, description: str = "", template: Optional[str] = None) -> World:
        """
        创建新世界
        
        Args:
            name: 世界名称
            description: 世界描述
            template: 模板名称（可选），可选值: "canon", "user_branch", None
        
        Returns:
            创建的World对象
        """
        world_id = self._generate_world_id(name)
        
        # 创建世界对象
        world = World(
            world_id=world_id,
            name=name,
            description=description
        )
        
        # 添加到列表
        self._worlds[world_id] = world
        self._save_worlds_list()
        
        # 创建世界数据目录
        world_data_dir = self.worlds_dir / world_id
        world_data_dir.mkdir(exist_ok=True)
        
        # 如果指定了模板，复制模板数据
        if template:
            self._copy_template(world_id, template)
        else:
            # 创建空的世界数据结构
            self._create_empty_world_data(world_id)
        
        return world
    
    def _copy_template(self, world_id: str, template: str):
        """从模板复制数据"""
        template_dir = os.path.join(os.path.dirname(self.storage_dir), template)
        world_data_dir = self.worlds_dir / world_id
        
        try:
            # 复制角色数据
            if os.path.exists(os.path.join(template_dir, "graphs", template)):
                graphs_src = os.path.join(template_dir, "graphs", template)
                graphs_dst = world_data_dir / "graphs"
                os.makedirs(graphs_dst, exist_ok=True)
                for file in os.listdir(graphs_src):
                    if file.endswith('.json'):
                        shutil.copy2(os.path.join(graphs_src, file), os.path.join(graphs_dst, file))
            
            # 复制世界状态数据
            if os.path.exists(os.path.join(template_dir, "world_graph", template)):
                wg_src = os.path.join(template_dir, "world_graph", template)
                wg_dst = world_data_dir / "world_graph"
                os.makedirs(wg_dst, exist_ok=True)
                for file in os.listdir(wg_src):
                    shutil.copy2(os.path.join(wg_src, file), os.path.join(wg_dst, file))
            
            print(f"✅ 从模板 '{template}' 复制数据到世界 '{world_id}'")
        except Exception as e:
            print(f"⚠️ 复制模板数据失败: {e}")
            # 如果复制失败，创建空数据
            self._create_empty_world_data(world_id)
    
    def _create_empty_world_data(self, world_id: str):
        """创建空的世界数据结构"""
        world_data_dir = self.worlds_dir / world_id
        
        # 创建必要的数据文件
        graphs_dir = world_data_dir / "graphs"
        graphs_dir.mkdir(exist_ok=True)
        
        # 创建空的角色数据
        characters_file = graphs_dir / "chapter_001.characters.json"
        with open(characters_file, 'w', encoding='utf-8') as f:
            json.dump({"characters": {}}, f, ensure_ascii=False, indent=2)
        
        # 创建空的关系数据
        relations_file = graphs_dir / "chapter_001.relations.json"
        with open(relations_file, 'w', encoding='utf-8') as f:
            json.dump({"nodes": [], "edges": []}, f, ensure_ascii=False, indent=2)
        
        # 创建世界状态
        wg_dir = world_data_dir / "world_graph"
        wg_dir.mkdir(exist_ok=True)
        
        state_file = wg_dir / "chapter_001.json"
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump({
                "chapter_id": 1,
                "time": 0,
                "events": [],
                "goals": {}
            }, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 为世界 '{world_id}' 创建空数据结构")
    
    def get_world(self, world_id: str) -> Optional[World]:
        """获取指定世界"""
        return self._worlds.get(world_id)
    
    def list_worlds(self) -> List[World]:
        """列出所有世界"""
        return list(self._worlds.values())
    
    def update_world(
        self,
        world_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[World]:
        """更新世界信息"""
        world = self._worlds.get(world_id)
        if not world:
            return None
        
        if name is not None:
            world.name = name
        if description is not None:
            world.description = description
        if metadata is not None:
            world.metadata.update(metadata)
        
        world.last_modified = datetime.now().isoformat()
        
        self._save_worlds_list()
        return world
    
    def delete_world(self, world_id: str) -> bool:
        """删除世界"""
        if world_id not in self._worlds:
            return False
        
        # 删除数据目录
        world_data_dir = self.worlds_dir / world_id
        if world_data_dir.exists():
            shutil.rmtree(world_data_dir)
        
        # 从列表中移除
        del self._worlds[world_id]
        self._save_worlds_list()
        
        return True
    
    def get_world_data_path(self, world_id: str) -> Optional[Path]:
        """获取世界数据路径"""
        if world_id not in self._worlds:
            return None
        return self.worlds_dir / world_id
    
    def export_world(self, world_id: str, export_path: str) -> bool:
        """导出世界到文件"""
        world_data_dir = self.get_world_data_path(world_id)
        if not world_data_dir:
            return False
        
        try:
            # 创建导出包
            import zipfile
            with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(world_data_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, world_data_dir)
                        zipf.write(file_path, arcname)
            
            return True
        except Exception as e:
            print(f"⚠️ 导出世界失败: {e}")
            return False
    
    def import_world(self, name: str, import_path: str, description: str = "") -> Optional[World]:
        """从文件导入世界"""
        try:
            # 创建新世界
            world_id = self._generate_world_id(name)
            world = World(
                world_id=world_id,
                name=name,
                description=description
            )
            
            self._worlds[world_id] = world
            self._save_worlds_list()
            
            # 解压到世界数据目录
            world_data_dir = self.worlds_dir / world_id
            world_data_dir.mkdir(exist_ok=True)
            
            import zipfile
            with zipfile.ZipFile(import_path, 'r') as zipf:
                zipf.extractall(world_data_dir)
            
            print(f"✅ 从文件导入世界 '{name}'")
            return world
        except Exception as e:
            print(f"⚠️ 导入世界失败: {e}")
            # 清理失败的数据
            if world_id in self._worlds:
                del self._worlds[world_id]
                self._save_worlds_list()
            return None
    
    def save_world_state(self, world_id: str, world_state: Dict) -> bool:
        """保存完整的世界状态（包括所有动态数据）"""
        world_data_dir = self.get_world_data_path(world_id)
        if not world_data_dir:
            return False
        
        try:
            # 保存时间、地点、事件
            self._save_world_state(world_data_dir, world_state)
            
            # 保存角色数据
            if "characters" in world_state:
                self._save_characters(world_data_dir, world_state["characters"])
            
            # 更新世界最后修改时间
            world = self._worlds.get(world_id)
            if world:
                world.last_modified = datetime.now().isoformat()
                self._save_worlds_list()
            
            return True
        except Exception as e:
            print(f"⚠️ 保存世界状态失败: {e}")
            return False
    
    def save_emotions(self, world_id: str, emotions: Dict) -> bool:
        """保存情感状态"""
        world_data_dir = self.get_world_data_path(world_id)
        if not world_data_dir:
            return False
        
        try:
            emotions_file = world_data_dir / "emotions.json"
            with open(emotions_file, 'w', encoding='utf-8') as f:
                json.dump(emotions, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"⚠️ 保存情感状态失败: {e}")
            return False
    
    def save_motivations(self, world_id: str, motivations: Dict) -> bool:
        """保存动机状态"""
        world_data_dir = self.get_world_data_path(world_id)
        if not world_data_dir:
            return False
        
        try:
            motivations_file = world_data_dir / "motivations.json"
            with open(motivations_file, 'w', encoding='utf-8') as f:
                json.dump(motivations, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"⚠️ 保存动机状态失败: {e}")
            return False
    
    def load_world_state(self, world_id: str) -> Optional[Dict]:
        """加载世界的完整状态"""
        world_data_dir = self.get_world_data_path(world_id)
        if not world_data_dir:
            return None
        
        try:
            state = {}
            
            # 加载世界状态
            state_file = world_data_dir / "world_graph" / "chapter_001.json"
            if state_file.exists():
                with open(state_file, 'r', encoding='utf-8') as f:
                    state.update(json.load(f))
            
            # 加载角色数据
            chars_file = world_data_dir / "graphs" / "chapter_001.characters.json"
            if chars_file.exists():
                with open(chars_file, 'r', encoding='utf-8') as f:
                    chars_data = json.load(f)
                    # 兼容处理：如果数据是 {"characters": {...}} 格式，提取内部结构
                    if isinstance(chars_data, dict) and "characters" in chars_data:
                        # 检查是否是旧的双重嵌套格式
                        inner_chars = chars_data["characters"]
                        # 如果inner_chars包含"attributes"等字段，说明这是单个角色的错误数据，应该使用整个结构
                        if isinstance(inner_chars, dict) and "attributes" in inner_chars:
                            state["characters"] = chars_data
                        else:
                            state["characters"] = chars_data["characters"]
                    else:
                        state["characters"] = chars_data
            
            # 加载情感状态
            emotions_file = world_data_dir / "emotions.json"
            if emotions_file.exists():
                with open(emotions_file, 'r', encoding='utf-8') as f:
                    state["emotions"] = json.load(f)
            
            # 加载动机状态
            motivations_file = world_data_dir / "motivations.json"
            if motivations_file.exists():
                with open(motivations_file, 'r', encoding='utf-8') as f:
                    state["motivations"] = json.load(f)
            
            return state
        except Exception as e:
            print(f"⚠️ 加载世界状态失败: {e}")
            return None
    
    def _save_characters(self, world_data_dir: Path, characters: Dict):
        """保存角色数据到文件"""
        graphs_dir = world_data_dir / "graphs"
        graphs_dir.mkdir(exist_ok=True)
        
        characters_file = graphs_dir / "chapter_001.characters.json"
        with open(characters_file, 'w', encoding='utf-8') as f:
            json.dump(characters, f, ensure_ascii=False, indent=2)
    
    def _save_relations(self, world_data_dir: Path, relations: Dict):
        """保存关系统据到文件"""
        graphs_dir = world_data_dir / "graphs"
        graphs_dir.mkdir(exist_ok=True)
        
        relations_file = graphs_dir / "chapter_001.relations.json"
        with open(relations_file, 'w', encoding='utf-8') as f:
            json.dump(relations, f, ensure_ascii=False, indent=2)
    
    def _save_world_state(self, world_data_dir: Path, state: Dict):
        """保存世界状态到文件"""
        wg_dir = world_data_dir / "world_graph"
        wg_dir.mkdir(exist_ok=True)
        
        state_file = wg_dir / "chapter_001.json"
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)