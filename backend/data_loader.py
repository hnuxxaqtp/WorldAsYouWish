#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据加载器 - 从文件加载世界数据
"""

import json
import os
import sys
from typing import Dict, Optional

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tkg_models import CharacterAttributes, RelationsSnapshot


class DataLoader:
    """数据加载器"""
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    def load_world_data(self, worldline_id: str = "canon") -> Dict:
        """加载世界数据
        
        Args:
            worldline_id: 世界线ID，用于 graphs/world_graph 模板数据
                         如果 base_dir 已设置为特定世界路径，则直接从该路径加载
        """
        world_data = {
            "worldline_id": worldline_id,
            "characters": {},
            "relations": {"nodes": [], "edges": []},
            "locations": {},
            "location_map": {},
            "goals": {},
            "initial_time": 0,
            "initial_events": []
        }
        
        # 加载角色数据
        chapter_id = 1  # 默认加载第一章
        
        # 检查是否是特定世界的目录（包含 graphs 和 world_graph）
        use_world_dir = os.path.exists(f"{self.base_dir}/graphs/chapter_{chapter_id:03d}.characters.json")
        
        if use_world_dir:
            # 直接从世界目录加载（base_dir 已经指向具体世界）
            char_path = f"{self.base_dir}/graphs/chapter_{chapter_id:03d}.characters.json"
            print(f"📂 加载角色数据: {char_path}")
        else:
            # 从项目根目录的多世界线数据加载
            char_path = f"{self.base_dir}/graphs/{worldline_id}/chapter_{chapter_id:03d}.characters.json"
            print(f"📂 加载角色数据: {char_path}")
        
        if os.path.exists(char_path):
            with open(char_path, 'r', encoding='utf-8') as f:
                char_data = json.load(f)
                for char_name, char_attrs_data in char_data.get("characters", {}).items():
                    world_data["characters"][char_name] = CharacterAttributes(**char_attrs_data)
                print(f"   ✅ 成功加载 {len(world_data['characters'])} 个角色")
        else:
            print(f"   ❌ 角色文件不存在: {char_path}")
        
        # 加载关系数据
        if use_world_dir:
            rel_path = f"{self.base_dir}/graphs/chapter_{chapter_id:03d}.relations.json"
        else:
            rel_path = f"{self.base_dir}/graphs/{worldline_id}/chapter_{chapter_id:03d}.relations.json"
        
        if os.path.exists(rel_path):
            with open(rel_path, 'r', encoding='utf-8') as f:
                rel_data = json.load(f)
                world_data["relations"] = {
                    "nodes": rel_data.get("nodes", []),
                    "edges": rel_data.get("edges", [])
                }
        
        # 加载章节状态（获取目标和地点信息）
        if use_world_dir:
            state_path = f"{self.base_dir}/world_graph/chapter_{chapter_id:03d}.json"
        else:
            state_path = f"{self.base_dir}/world_graph/{worldline_id}/chapter_{chapter_id:03d}.json"
        if os.path.exists(state_path):
            with open(state_path, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
                world_data["goals"] = state_data.get("goals", {})
                
                # 从事件中提取地点信息
                locations = set()
                for event in state_data.get("events", []):
                    if event.get("location"):
                        locations.add(event["location"])
                
                # 初始化地点数据
                for loc in locations:
                    world_data["locations"][loc] = {
                        "name": loc,
                        "description": f"故事中的地点：{loc}",
                        "type": "未知"
                    }
        
        # 如果没有地点数据，使用默认地点
        if not world_data["locations"]:
            world_data["locations"] = {
                "王都": {
                    "name": "王都",
                    "description": "故事的主要发生地",
                    "type": "城市"
                }
            }
        
        # 初始化角色位置（从章节状态或默认）
        # 可以从章节状态中提取角色位置，这里使用默认值
        
        return world_data
    
    def load_tkg_data(self, worldline_id: str = "canon", chapter_id: int = 1) -> list:
        """加载TKG数据"""
        tkg_path = f"{self.base_dir}/tkg/{worldline_id}/chapter_{chapter_id:03d}.tkg.jsonl"
        triples = []
        
        if os.path.exists(tkg_path):
            with open(tkg_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        triples.append(json.loads(line))
        
        return triples
    
    def load_chapter_state(self, worldline_id: str = "canon", chapter_id: int = 1) -> Optional[Dict]:
        """加载章节状态"""
        state_path = f"{self.base_dir}/world_graph/{worldline_id}/chapter_{chapter_id:03d}.json"
        
        if os.path.exists(state_path):
            with open(state_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return None

