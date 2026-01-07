#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import json
import os
from typing import List, Dict, Tuple, Optional
from openai import OpenAI
from narrative_state import NarrativeState
from state_extractor import extract_state_for_chapter, extract_tkg_for_chapter, extract_char_graph_for_chapter
from tkg_models import TKGEntry, CharactersSnapshot, RelationsSnapshot, CharacterAttributes


class NarrativeAgent:
    def __init__(self, file_path: str, api_key: str = None):
        """
        初始化叙事代理
        
        Args:
            file_path: 故事文件路径
            api_key: OpenAI API密钥
        """
        self.file_path = file_path
        self.chunks = []
        self.current_chunk_index = 0
        self.user_has_edited = False
        self.original_content = ""
        self.modified_content = ""
        
        # 设置OpenAI API
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            # 尝试从环境变量获取
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.client = OpenAI(api_key=api_key)
            else:
                self.client = None
        
        # 初始化章节状态相关
        self.canon_states_dir = "world_graph/canon"
        self.current_chapter_state = None
        
        # 初始化章节级修改机制
        self.edit_count = 0
        self.max_edits = 5
        self.chapter_original = ""  # 保存原始章节内容
        
        # 新增：世界线管理和目录初始化
        self.worldline_id = "canon"  # 默认世界线ID
        self.ensure_directories()
        
        self.load_and_process_file()
        self.ensure_canon_states()
    
    def ensure_directories(self):
        """确保必要的目录存在"""
        os.makedirs(f"tkg/{self.worldline_id}", exist_ok=True)
        os.makedirs(f"graphs/{self.worldline_id}", exist_ok=True)
        print(f"✅ 目录初始化完成: tkg/{self.worldline_id}, graphs/{self.worldline_id}")
    
    def load_and_process_file(self):
        """加载文件并处理内容"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.original_content = f.read()
                self.modified_content = self.original_content
                self.chapter_original = self.original_content  # 保存原始章节内容
            
            self.chunks = self.split_into_chunks(self.original_content)
            print(f"成功加载文件，共划分为 {len(self.chunks)} 个chunk")
        except Exception as e:
            print(f"加载文件失败: {e}")
    
    def split_into_chunks(self, content: str) -> List[str]:
        """
        按照昴来划分chunk
        
        Args:
            content: 原始内容
            
        Returns:
            划分后的chunk列表
        """
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        first_chunk = True
        
        for line in lines:
            current_chunk.append(line)
            
            # 如果遇到【昴】开头的行
            if line.strip().startswith('【昴】'):
                if first_chunk:
                    # 第一个chunk：从开始到第一个【昴】
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
                    first_chunk = False
                else:
                    # 后续chunk：从上一个【昴】到当前【昴】
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
        
        # 添加最后一个chunk（如果有剩余内容）
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks
    
    def classify_content(self) -> Dict[str, List[str]]:
        """
        将内容分类为已发生、正在发生、将要发生
        
        Returns:
            分类后的内容字典
        """
        # 根据用户当前交互状态来分类
        # 已发生：用户已经看过的chunk
        # 正在发生：当前正在交互的chunk
        # 将要发生：还未到达的chunk
        
        return {
            "已发生": self.chunks[:self.current_chunk_index],
            "正在发生": [self.chunks[self.current_chunk_index]] if self.current_chunk_index < len(self.chunks) else [],
            "将要发生": self.chunks[self.current_chunk_index + 1:] if self.current_chunk_index + 1 < len(self.chunks) else []
        }
    
    def is_editable_chunk(self, chunk_index: int) -> bool:
        """
        判断当前chunk是否可编辑（包含昴的内容）
        
        Args:
            chunk_index: chunk索引
            
        Returns:
            是否可编辑
        """
        if chunk_index >= len(self.chunks):
            return False
        
        chunk_content = self.chunks[chunk_index]
        return '【昴】' in chunk_content
    
    def get_current_chunk_content(self) -> str:
        """获取当前chunk的内容"""
        if self.current_chunk_index < len(self.chunks):
            return self.chunks[self.current_chunk_index]
        return ""
    
    def get_current_chunk_span(self) -> Optional[Tuple[int, int]]:
        """返回当前chunk在 self.modified_content 中的起止字符位置"""
        chunk = self.get_current_chunk_content()
        if not chunk:
            return None
        # 可能存在重复片段：优先从上一次位置附近查找可进一步优化
        start = self.modified_content.find(chunk)
        if start == -1:
            return None
        return (start, start + len(chunk))
    
    def display_current_chunk(self):
        """显示当前chunk内容"""
        if self.current_chunk_index >= len(self.chunks):
            print("故事已结束！")
            return
        
        chunk_content = self.get_current_chunk_content()
        print(f"\n=== 第 {self.current_chunk_index + 1} 个chunk ===")
        print(chunk_content)
        
        if self.is_editable_chunk(self.current_chunk_index):
            print("\n💡 这是昴的部分，你可以编辑！")
        else:
            print("\n📖 这是旁白部分，不可编辑")
    

    
    def call_llm(self, prompt: str) -> str:
        """
        调用LLM生成内容
        
        Args:
            prompt: 提示词
            
        Returns:
            LLM生成的内容
        """
        if not self.client:
            print("⚠️ 未设置OpenAI API密钥，使用默认内容")
            return "【旁白】故事继续发展...\n【昴】继续我的冒险！"
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "你是专业故事编辑。所有输出必须采用【旁白】【角色】的剧本格式，且只输出重写的后半部分。不要解释，不要加标题。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1200,
                temperature=0.2
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"LLM调用失败: {e}")
            return "【旁白】故事继续发展...\n【昴】继续我的冒险！"
    
    def save_to_file(self):
        """保存修改后的内容到文件"""
        try:
            updated_content = "\n\n".join(self.chunks)
            
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print("💾 内容已保存到文件！")
            
        except Exception as e:
            print(f"❌ 保存失败: {e}")
    
    def next_chunk(self):
        """移动到下一个chunk"""
        if self.current_chunk_index < len(self.chunks) - 1:
            self.current_chunk_index += 1
            self.display_current_chunk()
        else:
            print("🎉 故事已结束！")
    
    def previous_chunk(self):
        """移动到上一个chunk"""
        if self.current_chunk_index > 0:
            self.current_chunk_index -= 1
            self.display_current_chunk()
        else:
            print("📖 已经是第一个chunk了！")
    
    def show_classification(self):
        """显示内容分类"""
        classification = self.classify_content()
        
        print("\n=== 内容分类 ===")
        for category, chunks in classification.items():
            print(f"\n{category} ({len(chunks)}个chunk):")
            for i, chunk in enumerate(chunks[:3]):  # 只显示前3个
                print(f"  {i+1}. {chunk[:50]}...")
            if len(chunks) > 3:
                print(f"  ... 还有 {len(chunks) - 3} 个chunk")
    
    def ensure_canon_states(self):
        """确保canon状态快照存在"""
        if not os.path.exists(self.canon_states_dir):
            print("🔧 首次运行，正在生成canon状态快照...")
            self.build_canon_states()
        else:
            print("✅ canon状态快照已存在")
    
    def build_canon_states(self):
        """构建canon状态快照"""
        try:
            from build_chapter_states import build_states
            api_key = os.getenv('OPENAI_API_KEY')
            build_states(self.file_path, self.canon_states_dir, api_key)
            print("✅ canon状态快照构建完成")
        except Exception as e:
            print(f"❌ 构建canon状态失败: {e}")
    
    def get_current_chapter_id(self) -> int:
        """获取当前章节ID"""
        # 整个文件就是一个章节
        return 1
    
    def get_current_chapter_content(self) -> str:
        """获取当前章节的完整内容"""
        # 整个文件内容就是章节内容
        return self.modified_content
    
    def load_canon_state(self, chapter_id: int) -> Optional[NarrativeState]:
        """加载canon状态"""
        try:
            state_path = os.path.join(self.canon_states_dir, f"chapter_{chapter_id:03d}.json")
            if os.path.exists(state_path):
                with open(state_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return NarrativeState(**data)
        except Exception as e:
            print(f"❌ 加载canon状态失败: {e}")
        return None
    
    def load_character_data(self, chapter_id: int) -> tuple:
        """加载人物关系图和角色画像数据"""
        characters_data = {}
        relations_data = {}
        
        try:
            # 加载角色属性表
            char_path = f"graphs/canon/chapter_{chapter_id:03d}.characters.json"
            if os.path.exists(char_path):
                with open(char_path, 'r', encoding='utf-8') as f:
                    char_data = json.load(f)
                    characters_data = char_data.get("characters", {})
                print(f"✅ 已加载角色画像数据: {len(characters_data)} 个角色")
            else:
                print(f"⚠️ 未找到角色画像文件: {char_path}")
            
            # 加载关系图
            rel_path = f"graphs/canon/chapter_{chapter_id:03d}.relations.json"
            if os.path.exists(rel_path):
                with open(rel_path, 'r', encoding='utf-8') as f:
                    rel_data = json.load(f)
                    relations_data = {
                        "nodes": rel_data.get("nodes", []),
                        "edges": rel_data.get("edges", [])
                    }
                print(f"✅ 已加载关系图数据: {len(relations_data.get('edges', []))} 条关系")
            else:
                print(f"⚠️ 未找到关系图文件: {rel_path}")
                
        except Exception as e:
            print(f"❌ 加载人物数据失败: {e}")
        
        return characters_data, relations_data
    
    def format_character_data_for_prompt(self, characters_data: dict, relations_data: dict) -> str:
        """将人物数据格式化为提示词"""
        if not characters_data and not relations_data.get('edges'):
            return "⚠️ 未找到人物数据，将基于文本内容进行推理。"
        
        prompt_parts = []
        
        # 角色画像部分
        if characters_data:
            prompt_parts.append("【角色画像】")
            for char_name, char_attrs in characters_data.items():
                traits = char_attrs.get("traits", [])
                combat_power = char_attrs.get("combat_power", "未知")
                inventory = char_attrs.get("inventory", [])
                
                char_desc = f"- {char_name}:"
                if traits:
                    char_desc += f" 性格特质: {', '.join(traits)}"
                if combat_power != "未知":
                    char_desc += f" 战斗力: {combat_power}"
                if inventory:
                    char_desc += f" 持有物品: {', '.join(inventory)}"
                
                prompt_parts.append(char_desc)
        
        # 关系图部分
        edges = relations_data.get('edges', [])
        if edges:
            prompt_parts.append("\n【人物关系】")
            for edge in edges:
                a = edge.get('a', '')
                b = edge.get('b', '')
                rel_type = edge.get('type', '')
                score = edge.get('score', 0.0)
                evidence = edge.get('evidence', '')
                
                rel_desc = f"- {a} 与 {b}: {rel_type} (强度: {score:.2f})"
                if evidence:
                    rel_desc += f" - 证据: {evidence[:50]}..."
                
                prompt_parts.append(rel_desc)
        
        # 添加推理指导
        prompt_parts.append("\n【剧情推理指导】")
        prompt_parts.append("请根据以上人物数据推理剧情走向:")
        prompt_parts.append("1. 关系不好的角色之间达成合作的概率较低")
        prompt_parts.append("2. 战斗力弱的角色战胜战斗力强的角色概率较低")
        prompt_parts.append("3. 角色行为应符合其性格特质")
        prompt_parts.append("4. 关系强度影响角色间的互动方式")
        
        return "\n".join(prompt_parts)
    
    def extract_current_chapter_state(self) -> NarrativeState:
        """提取当前章节的状态"""
        chapter_id = self.get_current_chapter_id()
        chapter_content = self.get_current_chapter_content()
        title = f"第{chapter_id}章"
        
        print(f"🔍 正在提取第{chapter_id}章状态...")
        state = extract_state_for_chapter(chapter_id, title, chapter_content, self.client)
        self.current_chapter_state = state
        return state
    
    def save_chapter_state(self):
        """保存/提交当前章节状态"""
        print("💾 正在保存章节状态...")
        
        # 检查是否有修改，决定保存到哪个分支
        if self.user_has_edited or self.edit_count > 0:
            self.worldline_id = "user_branch"
            print("🔄 检测到用户修改，保存到user_branch分支")
        else:
            self.worldline_id = "canon"
            print("📖 无修改，保存到canon分支")
        
        # 确保目录存在
        self.ensure_directories()
        
        # 提取当前章节状态
        current_state = self.extract_current_chapter_state()
        
        # 加载canon状态进行对比
        chapter_id = self.get_current_chapter_id()
        canon_state = self.load_canon_state(chapter_id)
        
        if canon_state:
            print(f"📊 第{chapter_id}章状态对比:")
            print(f"  - 事件数: {len(current_state.events)} (canon: {len(canon_state.events)})")
            print(f"  - 关系数: {len(current_state.relations)} (canon: {len(canon_state.relations)})")
            print(f"  - 目标数: {len(current_state.goals)} (canon: {len(canon_state.goals)})")
            print(f"  - 道具数: {len(current_state.objects)} (canon: {len(canon_state.objects)})")
        else:
            print(f"⚠️  未找到第{chapter_id}章的canon状态")
        
        # 保存当前状态到对应分支
        states_dir = f"world_graph/{self.worldline_id}"
        os.makedirs(states_dir, exist_ok=True)
        
        state_path = os.path.join(states_dir, f"chapter_{chapter_id:03d}.json")
        with open(state_path, 'w', encoding='utf-8') as f:
            f.write(current_state.model_dump_json(indent=2))
        
        print(f"✅ 章节状态已保存到 {state_path}")
        
        # 新增：TKG和人物图抽取与落盘
        self.extract_and_save_tkg(chapter_id)
        self.extract_and_save_character_graphs(chapter_id)
        
        return current_state
    
    def extract_and_save_tkg(self, chapter_id: int):
        """抽取并保存章节TKG"""
        print("🔍 正在抽取章节TKG...")
        
        chapter_text = self.get_current_chapter_content()
        title = f"第{chapter_id}章"
        
        # 抽取TKG
        triples = extract_tkg_for_chapter(chapter_id, title, chapter_text, self.client)
        
        # 保存到JSONL文件
        tkg_path = f"tkg/{self.worldline_id}/chapter_{chapter_id:03d}.tkg.jsonl"
        with open(tkg_path, 'w', encoding='utf-8') as f:
            for triple in triples:
                f.write(triple.model_dump_json() + '\n')
        
        # 统计信息
        relation_counts = {}
        for triple in triples:
            relation_counts[triple.r] = relation_counts.get(triple.r, 0) + 1
        
        print(f"✅ TKG已保存到 {tkg_path}")
        print(f"📊 TKG统计: {len(triples)} 条记录")
        if relation_counts:
            top_relations = sorted(relation_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"🔗 关系分布 Top-5: {', '.join([f'{r}({c})' for r, c in top_relations])}")
    
    def extract_and_save_character_graphs(self, chapter_id: int):
        """抽取并保存人物图"""
        print("👥 正在抽取人物图...")
        
        chapter_text = self.get_current_chapter_content()
        title = f"第{chapter_id}章"
        
        # 加载上一章快照
        prev_characters = {}
        prev_relations = RelationsSnapshot(chapter_id=chapter_id-1, nodes=[], edges=[])
        
        if chapter_id > 1:
            prev_char_path = f"graphs/{self.worldline_id}/chapter_{chapter_id-1:03d}.characters.json"
            prev_rel_path = f"graphs/{self.worldline_id}/chapter_{chapter_id-1:03d}.relations.json"
            
            try:
                if os.path.exists(prev_char_path):
                    with open(prev_char_path, 'r', encoding='utf-8') as f:
                        prev_data = json.load(f)
                        for char_name, char_data in prev_data.get("characters", {}).items():
                            prev_characters[char_name] = CharacterAttributes(**char_data)
                
                if os.path.exists(prev_rel_path):
                    with open(prev_rel_path, 'r', encoding='utf-8') as f:
                        prev_rel_data = json.load(f)
                        prev_relations = RelationsSnapshot(**prev_rel_data)
            except Exception as e:
                print(f"⚠️ 加载上一章快照失败: {e}")
        
        # 抽取人物图
        char_snapshot, rel_snapshot = extract_char_graph_for_chapter(
            chapter_id, title, chapter_text, prev_characters, prev_relations, self.client
        )
        
        # 保存角色属性表
        char_path = f"graphs/{self.worldline_id}/chapter_{chapter_id:03d}.characters.json"
        with open(char_path, 'w', encoding='utf-8') as f:
            f.write(char_snapshot.model_dump_json(indent=2))
        
        # 保存关系图
        rel_path = f"graphs/{self.worldline_id}/chapter_{chapter_id:03d}.relations.json"
        with open(rel_path, 'w', encoding='utf-8') as f:
            f.write(rel_snapshot.model_dump_json(indent=2))
        
        print(f"✅ 人物图已保存:")
        print(f"  - 角色属性: {char_path}")
        print(f"  - 关系图: {rel_path}")
        print(f"📊 统计: {len(char_snapshot.characters)} 个角色, {len(rel_snapshot.edges)} 条关系")
    
    def show_tkg_summary(self):
        """显示本章TKG摘要"""
        chapter_id = self.get_current_chapter_id()
        
        # 优先检查user_branch，如果没有则检查canon
        tkg_paths = [
            f"tkg/user_branch/chapter_{chapter_id:03d}.tkg.jsonl",
            f"tkg/canon/chapter_{chapter_id:03d}.tkg.jsonl"
        ]
        
        tkg_path = None
        for path in tkg_paths:
            if os.path.exists(path):
                tkg_path = path
                break
        
        if not tkg_path:
            print("❌ 未找到本章TKG文件，请先运行 'state' 命令生成")
            return
        
        print(f"\n=== 第{chapter_id}章TKG摘要 ===")
        
        triples = []
        with open(tkg_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    triples.append(json.loads(line))
        
        print(f"📊 总记录数: {len(triples)}")
        
        # 统计关系分布
        relation_counts = {}
        entities = set()
        for triple in triples:
            relation_counts[triple['r']] = relation_counts.get(triple['r'], 0) + 1
            entities.add(triple['h'])
            entities.add(triple['t'])
        
        print(f"👥 涉及实体: {len(entities)} 个")
        print(f"🔗 关系类型: {len(relation_counts)} 种")
        
        if relation_counts:
            top_relations = sorted(relation_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"🔗 关系分布 Top-5:")
            for rel, count in top_relations:
                print(f"  - {rel}: {count} 次")
        
        # 显示前几条记录
        print(f"\n📝 前5条记录:")
        for i, triple in enumerate(triples[:5]):
            print(f"  {i+1}. {triple['h']} --{triple['r']}--> {triple['t']}")
            if 'evidence' in triple.get('meta', {}):
                evidence = triple['meta']['evidence'][:50]
                print(f"     证据: {evidence}...")
    
    def show_graph_summary(self):
        """显示本章人物图摘要"""
        chapter_id = self.get_current_chapter_id()
        
        # 优先检查user_branch，如果没有则检查canon
        char_paths = [
            f"graphs/user_branch/chapter_{chapter_id:03d}.characters.json",
            f"graphs/canon/chapter_{chapter_id:03d}.characters.json"
        ]
        rel_paths = [
            f"graphs/user_branch/chapter_{chapter_id:03d}.relations.json",
            f"graphs/canon/chapter_{chapter_id:03d}.relations.json"
        ]
        
        char_path = None
        rel_path = None
        
        for path in char_paths:
            if os.path.exists(path):
                char_path = path
                break
        
        for path in rel_paths:
            if os.path.exists(path):
                rel_path = path
                break
        
        if not char_path or not rel_path:
            print("❌ 未找到本章人物图文件，请先运行 'state' 命令生成")
            return
        
        print(f"\n=== 第{chapter_id}章人物图摘要 ===")
        
        # 加载角色属性
        with open(char_path, 'r', encoding='utf-8') as f:
            char_data = json.load(f)
        
        # 加载关系图
        with open(rel_path, 'r', encoding='utf-8') as f:
            rel_data = json.load(f)
        
        characters = char_data.get("characters", {})
        edges = rel_data.get("edges", [])
        
        print(f"👥 角色数: {len(characters)}")
        print(f"🔗 关系边数: {len(edges)}")
        
        # 显示角色属性
        print(f"\n👤 角色属性:")
        for char_name, char_attrs in characters.items():
            print(f"  - {char_name}:")
            print(f"    战斗力: {char_attrs.get('combat_power', '未知')}")
            print(f"    物品: {', '.join(char_attrs.get('inventory', []))}")
            print(f"    特质: {', '.join(char_attrs.get('traits', []))}")
        
        # 显示关系边
        print(f"\n🔗 关系边:")
        for edge in edges[:10]:  # 只显示前10条
            print(f"  - {edge['a']} --{edge['type']}({edge['score']:.2f})--> {edge['b']}")
            if edge.get('evidence'):
                evidence = edge['evidence'][:50]
                print(f"    证据: {evidence}...")
        
        if len(edges) > 10:
            print(f"  ... 还有 {len(edges) - 10} 条关系边")
    
    def find_editable_positions(self) -> List[Tuple[int, int, str]]:
        """
        找到所有可编辑的【昴】位置
        
        Returns:
            可编辑位置列表，每个元素为 (start_pos, end_pos, content)
        """
        editable_positions = []
        lines = self.modified_content.split('\n')
        
        for i, line in enumerate(lines):
            if line.strip().startswith('【昴】'):
                # 找到这个【昴】行的开始和结束位置
                start_pos = sum(len(lines[j]) + 1 for j in range(i))
                end_pos = start_pos + len(line)
                content = line
                editable_positions.append((start_pos, end_pos, content))
        
        return editable_positions
    
    def edit_chapter(self, user_edit: str, position_index: Optional[int] = None):
        """
        编辑章节中的【昴】部分
        
        Args:
            user_edit: 用户编辑的内容
            position_index: 要编辑的【昴】位置索引（None表示自动选择当前chunk内的【昴】）
        """
        if self.edit_count >= self.max_edits:
            print(f"❌ 已达到最大修改次数限制 ({self.max_edits} 次)")
            return
        
        editable_positions = self.find_editable_positions()
        if not editable_positions:
            print("❌ 未找到可编辑的【昴】内容")
            return
        
        # 自动选择"当前chunk内"的【昴】
        if position_index is None:
            span = self.get_current_chunk_span()
            if not span:
                print("❌ 无法定位当前chunk在全文中的位置")
                return
            cstart, cend = span
            # 在当前chunk范围内选择第一个【昴】
            in_chunk = [(s, e, c) for (s, e, c) in editable_positions if s >= cstart and e <= cend]
            if not in_chunk:
                print("📖 当前chunk为旁白或不含【昴】，不可在此处编辑")
                return
            start_pos, end_pos, original_content = in_chunk[0]
        else:
            if position_index >= len(editable_positions):
                print(f"❌ 位置索引超出范围，共有 {len(editable_positions)} 个可编辑位置")
                return
            start_pos, end_pos, original_content = editable_positions[position_index]
        
        # 验证用户编辑内容是否包含【昴】
        if not user_edit.strip().startswith('【昴】'):
            print("❌ 编辑内容必须以【昴】开头")
            return
        
        # 更新内容
        self.modified_content = (
            self.modified_content[:start_pos] + 
            user_edit + 
            self.modified_content[end_pos:]
        )
        
        self.edit_count += 1
        self.user_has_edited = True  # 标记用户已进行编辑
        print(f"✅ 第 {self.edit_count} 次编辑成功！")
        
        # 调用LLM重写后续剧情
        self.rewrite_remaining_chapter(start_pos + len(user_edit))
        
        # 重新分割chunks
        self.chunks = self.split_into_chunks(self.modified_content)
    
    def rewrite_remaining_chapter(self, edit_position: int):
        """
        基于用户修改重写章节的后续部分
        
        Args:
            edit_position: 修改结束的位置
        """
        try:
            # 构建重写提示
            prompt = self.build_rewrite_prompt(edit_position)
            
            # 调用LLM重写
            rewritten_content = self.call_llm(prompt)
            
            # 更新章节内容
            self.modified_content = (
                self.modified_content[:edit_position] + 
                "\n" + 
                rewritten_content
            )
            
            # 将当前版本作为下一轮的"基线"
            self.chapter_original = self.modified_content
            
            print("🤖 LLM已重写章节后续剧情！")
            
        except Exception as e:
            print(f"❌ LLM重写失败: {e}")
    
    def build_rewrite_prompt(self, edit_position: int) -> str:
        """构建重写提示"""
        # 以"当前最新文本"为基线
        before_edit = self.modified_content[:edit_position]
        
        # 找到用户修改的【昴】内容
        user_edit_text = ""
        lines = before_edit.split('\n')
        for line in reversed(lines):
            if line.strip().startswith('【昴】'):
                user_edit_text = line
                break
        
        # 获取更长的上下文，避免断层
        ctx_window = 1200
        edit_context = before_edit[max(0, len(before_edit)-ctx_window):]
        
        current_full = self.modified_content
        
        # 加载人物数据
        chapter_id = self.get_current_chapter_id()
        characters_data, relations_data = self.load_character_data(chapter_id)
        character_prompt = self.format_character_data_for_prompt(characters_data, relations_data)
        
        return f"""你是一个小说叙事协作者，负责在保持剧情连贯与角色设定的前提下，根据用户提供的编辑内容，对当前章节的后续段落进行调整。

【任务目标】
根据用户在本章节中的修改，对本章节剩余部分进行必要的重写，使其符合用户修改后的语境、动机和节奏。

【硬性要求】
1. 必须尊重用户提供的修改内容；
2. 重写仅限当前章节中"修改位置之后的部分"，前文保留；
3. 重写内容需保持与章节已有剧情的因果一致性；
4. 不得引入与设定冲突的事件、人物行为或世界观变动；
5. 所有角色言行应符合其原始性格设定；
6. 必须严格使用【旁白】【角色】这样的剧本格式输出；
7. 章节生成内容的叙述视角、语体与节奏须与前文保持统一（不得切换为说明文或纲要）；
8. 不应破坏原章节的结局目标:寻找徽章，如最终冲突/转折等；
9. 续写应从用户修改之处无缝承接，第一句必须能与该句主语/指代自然衔接；不得开启新场景或新人物，除非先收束当前场景；
10. **重要**: 必须参考人物关系图和角色画像来决定剧情走向，确保角色行为符合其设定。

【人物数据参考】
{character_prompt}

【输入信息】
1. 当前章节内容（最新全文，已包含历次修改与重写）：
{current_full}

2. 用户第 {self.edit_count} 次修改（用户修改的片段）：
{user_edit_text}

3. 用户修改对应的原始位置（上下文）：
{edit_context}

【生成要求】
请你基于用户修改和人物数据，重写"该位置之后的章节内容"，使其与修改内容保持连贯，并最大限度保留原有章节结构节奏。

**特别注意**: 
- 关系不好的角色之间达成合作的概率较低
- 战斗力弱的角色战胜战斗力强的角色概率较低  
- 角色行为必须符合其性格特质
- 关系强度影响角色间的互动方式

生成输出请仅包括章节的"后半部分重写"，无需重复前文内容。"""
    
    def show_editable_positions(self):
        """显示所有可编辑的【昴】位置"""
        editable_positions = self.find_editable_positions()
        
        if not editable_positions:
            print("❌ 未找到可编辑的【昴】内容")
            return
        
        print(f"\n=== 可编辑的【昴】位置 ({len(editable_positions)} 个) ===")
        for i, (start_pos, end_pos, content) in enumerate(editable_positions):
            print(f"{i+1}. 位置 {start_pos}-{end_pos}: {content[:50]}...")
    
    def reset_chapter(self):
        """重置章节到原始状态"""
        self.modified_content = self.chapter_original
        self.edit_count = 0
        self.chunks = self.split_into_chunks(self.modified_content)
        print("🔄 章节已重置到原始状态")
    
    def display_chapter(self):
        """显示当前章节内容"""
        print(f"\n=== 当前章节内容 ===")
        print(f"修改次数: {self.edit_count}/{self.max_edits}")
        print(f"内容长度: {len(self.modified_content)} 字符")
        print("=" * 50)
        print(self.modified_content)
        print("=" * 50)
    
    def run_interactive_mode(self):
        """运行交互模式"""
        print("🎭 欢迎使用Agent叙事交互系统！")
        print("=" * 50)
        
        # 显示内容分类
        self.show_classification()
        
        # 显示第一个chunk
        self.display_current_chunk()
        
        while True:
            print("\n" + "=" * 50)
            print("可用命令:")
            print("n/next - 下一个chunk")
            print("p/prev - 上一个chunk")
            print("ce/chapter_edit <内容> - 章节级编辑（重写后续剧情）")
            print("p/positions - 显示可编辑的【昴】位置")
            print("d/display - 显示完整章节内容")
            print("r/reset - 重置章节到原始状态")
            print("s/save - 保存到文件")
            print("c/classify - 显示内容分类")
            print("state - 保存/提交本章状态快照")
            print("tkg - 显示本章TKG摘要")
            print("graph - 显示本章人物图摘要")
            print("q/quit - 退出")
            print("=" * 50)
            
            command = input("请输入命令: ").strip().lower()
            
            if command in ['q', 'quit']:
                print("👋 再见！")
                break
            elif command in ['n', 'next']:
                self.next_chunk()
            elif command in ['p', 'prev']:
                self.previous_chunk()
            elif command in ['s', 'save']:
                self.save_to_file()
            elif command.startswith(('ce', 'chapter_edit')):
                if command.startswith('chapter_edit '):
                    edit_content = command[13:]
                else:
                    edit_content = input("请输入章节编辑内容（必须以【昴】开头）: ")
                self.edit_chapter(edit_content, position_index=None)
            elif command in ['p', 'positions']:
                self.show_editable_positions()
            elif command in ['d', 'display']:
                self.display_chapter()
            elif command in ['r', 'reset']:
                self.reset_chapter()
            elif command in ['c', 'classify']:
                self.show_classification()
            elif command == 'state':
                self.save_chapter_state()
            elif command == 'tkg':
                self.show_tkg_summary()
            elif command == 'graph':
                self.show_graph_summary()
            else:
                print("❌ 未知命令，请重试！")


def main():
    """主函数"""
    print("🎭 Agent叙事交互系统")
    print("=" * 50)
    
    # 检查API密钥
    api_key = input("请输入OpenAI API密钥（或按回车跳过）: ").strip()
    if not api_key:
        api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("⚠️  警告：未设置API密钥，LLM功能将不可用！")
    
    # 创建Agent实例
    agent = NarrativeAgent("Chapter1-3.txt", api_key)
    
    # 运行交互模式
    agent.run_interactive_mode()


if __name__ == "__main__":
    main()
