#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小说知识库系统 - 从小说文本中提取并存储知识供检索使用
"""

import json
import re
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path
import hashlib
from openai import OpenAI


class NovelKnowledgeBase:
    """小说知识库"""
    
    def __init__(self, storage_dir: str = None, llm_client: OpenAI = None):
        """初始化知识库"""
        if storage_dir is None:
            import os
            self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            storage_dir = os.path.join(self.base_dir, "novel_kb")
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # LLM客户端（用于智能提取）
        self.llm_client = llm_client
        
        # 知识库数据
        self.characters: Dict[str, Dict] = {}  # 角色信息
        self.locations: Dict[str, Dict] = {}   # 地点信息
        self.events: List[Dict] = []            # 事件列表
        self.scenes: List[Dict] = []             # 场景列表
        self.summaries: List[Dict] = []         # 段落摘要
        self.metadata: Dict[str, Any] = {}       # 元数据
        
        self.knowledge_file = self.storage_dir / "knowledge_base.json"
        self.chunks_file = self.storage_dir / "text_chunks.jsonl"
    
    def from_novel_text(self, text: str, novel_name: str = "未命名小说") -> bool:
        """从小说文本构建知识库"""
        try:
            print(f"📖 开始从小说文本构建知识库: {novel_name}")
            print(f"   文本长度: {len(text)} 字符")
            
            # 清空旧数据
            self.clear()
            print("   ✓ 已清空旧数据")
            
            # 保存元数据
            self.metadata = {
                "novel_name": novel_name,
                "created_at": datetime.now().isoformat(),
                "total_length": len(text),
                "total_paragraphs": len([p for p in text.split('\n\n') if p.strip()])
            }
            print("   ✓ 元数据已保存")
            
            # 提取各个维度的知识
            print("   📊 开始提取角色...")
            self._extract_characters(text)
            print(f"   ✓ 角色提取完成: {len(self.characters)} 个")
            
            print("   🏛️  开始提取地点...")
            self._extract_locations(text)
            print(f"   ✓ 地点提取完成: {len(self.locations)} 个")
            
            print("   ⚡ 开始提取事件...")
            self._extract_events(text)
            print(f"   ✓ 事件提取完成: {len(self.events)} 个")
            
            print("   📝 开始分割文本块...")
            self._split_into_chunks(text)
            print(f"   ✓ 文本块分割完成: {len(self.chunks) if hasattr(self, 'chunks') else 0} 个")
            
            print("   📄 开始生成摘要...")
            self._generate_summaries(text)
            print(f"   ✓ 摘要生成完成: {len(self.summaries)} 段")
            
            # 保存知识库
            print("   💾 开始保存知识库...")
            save_success = self.save()
            if not save_success:
                print("   ❌ 保存知识库失败!")
                return False
            print("   ✓ 知识库保存成功")
            
            print(f"✅ 知识库构建完成!")
            print(f"   - 角色: {len(self.characters)} 个")
            print(f"   - 地点: {len(self.locations)} 个")
            print(f"   - 事件: {len(self.events)} 个")
            print(f"   - 场景: {len(self.chunks) if hasattr(self, 'chunks') else 0} 个")
            print(f"   - 段落: {len(self.summaries)} 段")
            
            return True
        except Exception as e:
            print(f"❌ 构建知识库失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _extract_characters(self, text: str):
        """提取角色信息（优先使用AI，降级到正则）"""
        # 优先尝试AI提取
        if self.llm_client:
            try:
                print("🤖 使用AI智能提取角色信息...")
                ai_result = self._extract_characters_with_ai(text)
                if ai_result:
                    # AI成功提取，合并到characters字典
                    for char in ai_result:
                        name = char["name"]
                        first_pos = text.find(name)
                        if first_pos != -1:
                            self.characters[name] = {
                                "name": name,
                                "first_mention": first_pos,
                                "description": char.get("description", ""),
                                "traits": char.get("traits", []),
                                "role": char.get("role", ""),
                                "mentions": text.count(name)
                            }
                    print(f"✅ AI提取到 {len(ai_result)} 个角色")
                    return
            except Exception as e:
                print(f"⚠️ AI提取失败，降级到正则表达式: {e}")
        
        # 降级方案：使用正则表达式
        print("📝 使用正则表达式提取角色信息...")
        self._extract_characters_with_regex(text)
    
    def _extract_locations(self, text: str):
        """提取地点信息（优先使用AI，降级到正则）"""
        # 优先尝试AI提取
        if self.llm_client:
            try:
                print("🤖 使用AI智能提取地点信息...")
                ai_result = self._extract_locations_with_ai(text)
                if ai_result:
                    # AI成功提取
                    for loc in ai_result:
                        name = loc["name"]
                        first_pos = text.find(name)
                        if first_pos != -1:
                            self.locations[name] = {
                                "name": name,
                                "first_mention": first_pos,
                                "description": loc.get("description", ""),
                                "type": loc.get("type", ""),
                                "mentions": text.count(name)
                            }
                    print(f"✅ AI提取到 {len(ai_result)} 个地点")
                    return
            except Exception as e:
                print(f"⚠️ AI提取失败，降级到正则表达式: {e}")
        
        # 降级方案：使用正则表达式
        print("📝 使用正则表达式提取地点信息...")
        self._extract_locations_with_regex(text)
    
    def _extract_events(self, text: str):
        """提取事件信息"""
        # 事件动作词
        action_markers = ['攻击', '击败', '遇见', '杀死', '救下', '发现', '找到', '夺回', '摧毁', '破坏']
        
        for action in action_markers:
            # 提取与动作相关的句子
            sentences = re.split(r'[。！？\n]', text)
            for i, sentence in enumerate(sentences):
                if action in sentence:
                    # 提取相关角色和地点
                    chars = [c for c in self.characters.keys() if c in sentence]
                    locs = [l for l in self.locations.keys() if l in sentence]
                    
                    if chars or locs:
                        self.events.append({
                            "type": action,
                            "description": sentence.strip(),
                            "characters": chars,
                            "locations": locs,
                            "position": len(''.join(sentences[:i]))
                        })
    
    def _split_into_chunks(self, text: str, chunk_size: int = 500):
        """将文本分割成可检索的片段"""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        chunks = []
        for i in range(0, len(paragraphs), 3):  # 每次取3个段落
            chunk_paras = paragraphs[i:i+3]
            chunk_text = '\n\n'.join(chunk_paras)
            
            # 计算chunk的向量表示的简单模拟（使用词频）
            words = re.findall(r'[\u4e00-\u9fa5]+', chunk_text)
            vector = list(set(words[:50]))  # 取前50个不同的词作为向量
            
            chunks.append({
                "id": len(chunks),
                "text": chunk_text,
                "vector": vector,
                "paragraph_indices": [i + j for j in range(len(chunk_paras))],
                "length": len(chunk_text)
            })
        
        self.chunks = chunks
    
    def _generate_summaries(self, text: str):
        """为每个段落生成摘要"""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        for para in paragraphs:
            # 简单的摘要：取前两句话
            sentences = re.split(r'[。！？]', para)
            summary = ''.join(sentences[:2]) if len(sentences) > 2 else para
            
            self.summaries.append({
                "original": para,
                "summary": summary[:200],
                "length": len(para)
            })
    
    def retrieve_relevant_content(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """根据查询检索相关内容"""
        # 简单的关键词匹配检索
        query_words = set(re.findall(r'[\u4e00-\u9fa5]{2,}', query))
        
        results = {
            "characters": [],
            "locations": [],
            "events": [],
            "scenes": [],
            "summaries": []
        }
        
        # 检索角色
        for name, char_info in self.characters.items():
            score = 0
            for word in query_words:
                if word in char_info["name"] or word in char_info["description"]:
                    score += 1
            if score > 0:
                results["characters"].append({**char_info, "relevance_score": score})
        
        # 检索地点
        for name, loc_info in self.locations.items():
            score = sum(1 for word in query_words if word in loc_info["name"])
            if score > 0:
                results["locations"].append({**loc_info, "relevance_score": score})
        
        # 检索事件
        for event in self.events:
            score = sum(1 for word in query_words if word in event["description"])
            if score > 0:
                results["events"].append({**event, "relevance_score": score})
        
        # 检索场景片段
        if hasattr(self, 'chunks'):
            for chunk in self.chunks:
                score = sum(1 for word in query_words if word in chunk["text"])
                if score > 0:
                    results["scenes"].append({
                        "id": chunk["id"],
                        "text": chunk["text"][:300],
                        "relevance_score": score
                    })
        
        # 检索摘要
        for summary in self.summaries:
            score = sum(1 for word in query_words if word in summary["original"])
            if score > 0:
                results["summaries"].append({
                    "original": summary["original"][:300],
                    "summary": summary["summary"],
                    "relevance_score": score
                })
        
        # 排序并返回前top_k个
        for key in results.keys():
            results[key] = sorted(results[key], key=lambda x: x.get("relevance_score", 0), reverse=True)[:top_k]
        
        return results
    
    def get_context_for_generation(self, context_type: str, keywords: List[str] = None) -> str:
        """获取用于LLM生成的上下文"""
        query = ' '.join(keywords or [])
        relevant = self.retrieve_relevant_content(query, top_k=3)
        
        contexts = []
        
        if context_type in ["character", "all"] and relevant["characters"]:
            contexts.append("【角色信息】")
            for char in relevant["characters"]:
                contexts.append(f"- {char['name']}: {char['description']}")
        
        if context_type in ["location", "all"] and relevant["locations"]:
            contexts.append("【地点信息】")
            for loc in relevant["locations"]:
                contexts.append(f"- {loc['name']}: {loc['description']}")
        
        if context_type in ["event", "all"] and relevant["events"]:
            contexts.append("【重要事件】")
            for event in relevant["events"]:
                contexts.append(f"- {event['description']}")
        
        if context_type in ["scene", "all"] and relevant["scenes"]:
            contexts.append("【相关场景】")
            for scene in relevant["scenes"][:3]:
                contexts.append(f"- {scene['text']}")
        
        return '\n'.join(contexts) if contexts else "暂无相关背景信息"
    
    def save(self) -> bool:
        """保存知识库到文件"""
        try:
            data = {
                "metadata": self.metadata,
                "characters": self.characters,
                "locations": self.locations,
                "events": self.events,
                "scenes": self.scenes
            }
            
            with open(self.knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 保存文本片段
            with open(self.chunks_file, 'w', encoding='utf-8') as f:
                for chunk in getattr(self, 'chunks', []):
                    # 不保存向量，节省空间
                    chunk_copy = {k: v for k, v in chunk.items() if k != 'vector'}
                    f.write(json.dumps(chunk_copy, ensure_ascii=False) + '\n')
            
            # 保存摘要
            summaries_file = self.storage_dir / "summaries.json"
            with open(summaries_file, 'w', encoding='utf-8') as f:
                json.dump(self.summaries, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"❌ 保存知识库失败: {e}")
            return False
    
    def load(self) -> bool:
        """从文件加载知识库"""
        try:
            if not self.knowledge_file.exists():
                return False
            
            with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.metadata = data.get("metadata", {})
                self.characters = data.get("characters", {})
                self.locations = data.get("locations", {})
                self.events = data.get("events", [])
                self.scenes = data.get("scenes", [])
            
            # 加载文本片段
            if self.chunks_file.exists():
                self.chunks = []
                with open(self.chunks_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            self.chunks.append(json.loads(line))
            
            # 加载摘要
            summaries_file = self.storage_dir / "summaries.json"
            if summaries_file.exists():
                with open(summaries_file, 'r', encoding='utf-8') as f:
                    self.summaries = json.load(f)
            
            return True
        except Exception as e:
            print(f"❌ 加载知识库失败: {e}")
            return False
    
    def clear(self):
        """清空知识库"""
        self.characters.clear()
        self.locations.clear()
        self.events.clear()
        self.scenes.clear()
        self.summaries.clear()
        self.metadata.clear()
        if hasattr(self, 'chunks'):
            self.chunks.clear()
    
    def get_stats(self) -> Dict:
        """获取知识库统计信息"""
        return {
            "novel_name": self.metadata.get("novel_name", "未命名"),
            "characters_count": len(self.characters),
            "locations_count": len(self.locations),
            "events_count": len(self.events),
            "scenes_count": len(getattr(self, 'chunks', [])),
            "summaries_count": len(self.summaries),
            "total_length": self.metadata.get("total_length", 0)
        }
    
    def get_statistics(self) -> Dict:
        """获取知识库统计信息（兼容调用）"""
        stats = self.get_stats()
        
        # 添加排序后的角色和地点列表
        top_characters = sorted(
            self.characters.keys(),
            key=lambda x: self.characters[x].get('mentions', 0),
            reverse=True
        )
        
        top_locations = sorted(
            self.locations.keys(),
            key=lambda x: self.locations[x].get('mentions', 0),
            reverse=True
        )
        
        return {
            **stats,
            "top_characters": top_characters,
            "top_locations": top_locations
        }
    
    def to_dict(self) -> Dict:
        """将知识库转换为字典"""
        return {
            "metadata": self.metadata,
            "characters": self.characters,
            "locations": self.locations,
            "events": self.events,
            "scenes": getattr(self, 'chunks', []),
            "summaries": self.summaries
        }
    
    def _extract_characters_with_ai(self, text: str) -> Optional[List[Dict]]:
        """使用AI提取角色信息"""
        if not self.llm_client:
            return None
            
        # 截取前3000字进行分析（避免token过长）
        sample_text = text[:3000] if len(text) > 3000 else text
        
        prompt = f"""请分析以下小说片段，提取其中的主要角色信息。

小说文本片段：
---
{sample_text}
---

请以JSON格式返回角色列表，每个角色包含：
- name: 角色名称
- description: 角色的简要描述（50-100字）
- traits: 角色特征（列表，如：["勇敢", "善良"]）
- role: 角色类型（如：主角、配角、路人等）

只需要返回JSON数组，不要有其他说明文字。格式必须符合严格JSON规范。
至少提取3-5个重要角色。

示例格式：
[{{"name": "角色名", "description": "描述...", "traits": ["特征1", "特征2"], "role": "主角"}}]"""
        
        try:
            print(f"   正在调用 SiliconFlow API (超时时间: 60秒)...")
            response = self.llm_client.chat.completions.create(
                model="Qwen/Qwen2.5-7B-Instruct",
                messages=[
                    {"role": "system", "content": "你是一个专业的小说分析助手，擅长从文本中提取角色信息。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000,
                timeout=60.0  # 添加60秒超时
            )
            
            result_text = response.choices[0].message.content.strip()
            print(f"   API 响应长度: {len(result_text)} 字符")
            
            # 提取JSON（可能被markdown代码块包裹）
            json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(0)
            
            characters_data = json.loads(result_text)
            print(f"   ✅ AI 提取成功: {len(characters_data)} 个角色")
            return characters_data
            
        except Exception as e:
            print(f"❌ AI角色提取失败: {e}")
            print(f"   错误类型: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_characters_with_regex(self, text: str):
        """使用正则表达式提取角色信息（降级方案）"""
        # 常见的角色出场模式
        patterns = [
            r'([\u4e00-\u9fa5]{2,4})(?:说|道|回答|问|笑道|叹道|说道)',
            r'([\u4e00-\u9fa5]{2,4})[，:：](?:她|他|它)',
        ]
        
        # 提取可能的角色名
        potential_chars = set()
        for pattern in patterns:
            try:
                matches = re.finditer(pattern, text)
                for match in matches:
                    name = match.group(1)
                    if len(name) >= 2 and len(name) <= 4:
                        potential_chars.add(name)
            except Exception as e:
                print(f"警告: 正则匹配失败: {e}")
        
        # 对角色名进行过滤（排除常见非角色词）
        exclude_words = {'那个', '这个', '什么', '如何', '因为', '所以', '而且', '但是', '如果'}
        potential_chars = {c for c in potential_chars if c not in exclude_words}
        
        # 查找每个角色的描述
        for name in potential_chars:
            # 查找角色首次出现的位置
            first_pos = text.find(name)
            if first_pos == -1:
                continue
            
            # 提取上下文（前后200字）
            context_start = max(0, first_pos - 200)
            context_end = min(len(text), first_pos + len(name) + 200)
            context = text[context_start:context_end].replace('\n', ' ')
            
            self.characters[name] = {
                "name": name,
                "first_mention": first_pos,
                "description": context[:150],
                "traits": [],
                "role": "未知",
                "mentions": text.count(name)
            }
    
    def _extract_locations_with_ai(self, text: str) -> Optional[List[Dict]]:
        """使用AI提取地点信息"""
        if not self.llm_client:
            return None
            
        # 截取前3000字进行分析
        sample_text = text[:3000] if len(text) > 3000 else text
        
        prompt = f"""请分析以下小说片段，提取其中的主要地点信息。

小说文本片段：
---
{sample_text}
---

请以JSON格式返回地点列表，每个地点包含：
- name: 地点名称
- description: 地点的简要描述（50-100字）
- type: 地点类型（如：城市、村庄、建筑、自然景观等）

只需要返回JSON数组，不要有其他说明文字。格式必须符合严格JSON规范。
至少提取3-5个重要地点。

示例格式：
[{{"name": "地点名", "description": "描述...", "type": "城市"}}]"""
        
        try:
            print(f"   正在调用 SiliconFlow API (超时时间: 60秒)...")
            response = self.llm_client.chat.completions.create(
                model="Qwen/Qwen2.5-7B-Instruct",
                messages=[
                    {"role": "system", "content": "你是一个专业的小说场景分析助手，擅长从文本中提取地点信息。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000,
                timeout=60.0  # 添加60秒超时
            )
            
            result_text = response.choices[0].message.content.strip()
            print(f"   API 响应长度: {len(result_text)} 字符")
            
            # 提取JSON
            json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(0)
            
            locations_data = json.loads(result_text)
            print(f"   ✅ AI 提取成功: {len(locations_data)} 个地点")
            return locations_data
            
        except Exception as e:
            print(f"❌ AI地点提取失败: {e}")
            print(f"   错误类型: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_locations_with_regex(self, text: str):
        """使用正则表达式提取地点信息（降级方案）"""
        # 地点关键词
        location_markers = ['在', '来到', '进入', '离开', '前往', '返回', '身处', '站在']
        
        # 提取地点模式
        for marker in location_markers:
            pattern = f'{marker}([\u4e00-\u9fa5]{2,10}(?:市|镇|村|城|山|河|路|街|房|屋|阁|庙|殿|洞|森林|草原|海滩|港口|边境|平原|峡谷)'
            try:
                matches = re.finditer(pattern, text)
                for match in matches:
                    location = match.group(1) + match.group(0)[match.end(1):]
                    if len(location) >= 2 and location not in self.locations:
                        pos = match.start()
                        context_start = max(0, pos - 100)
                        context_end = min(len(text), pos + len(match.group(0)) + 100)
                        self.locations[location] = {
                            "name": location,
                            "first_mention": pos,
                            "description": text[context_start:context_end].replace('\n', ' ')[:100],
                            "type": "未知",
                            "mentions": text.count(location)
                        }
            except Exception as e:
                print(f"警告: 正则匹配失败: {e}")