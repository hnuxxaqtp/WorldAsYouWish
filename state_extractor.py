import json, os, time
from typing import Optional, List, Dict, Any, Tuple
from openai import OpenAI
from narrative_state import NarrativeState, ValidationError
from tkg_models import TKGEntry, CharactersSnapshot, RelationsSnapshot, CharacterAttributes, RelationEdge

SYSTEM_PROMPT = (
    "你是叙事信息抽取器。严格输出 JSON，不要任何多余文字。"
    "目标：从输入章节抽取 events/relations/goals/objects。"
    "要求："
    "1) 事件粒度为'谁-做了什么-对谁/什么-意图'，避免句法碎片；"
    "2) relations 至少覆盖核心角色对；score ∈ [0,1] 越大关系越强；"
    "3) goals 仅写本章明确陈述或强暗示的角色目标；"
    "4) objects 只列关键设定/道具及其状态（例如'死亡回归: 已激活'）；"
    "5) 字段缺失用 null 或空数组；"
)

USER_PROMPT_TEMPLATE = """请从以下章节抽取叙事状态。只输出符合下述 JSON 模式的对象：
{{
  "events":[{{"who":"", "action":"", "target":null, "goal":null, "polarity":0, "time":null, "location":null, "precond":null, "effect":null}}],
  "relations":[{{"a":"", "b":"", "type":"盟友|对立|亲密|上下级|债务|同事|陌生|家人|同伴", "score":0.0}}],
  "goals":{{"角色名":["目标1","目标2"]}},
  "objects":{{"道具或设定":"状态/持有者/位置 等简短描述"}}
}}
章节文本：
{chapter_text}
"""

# TKG抽取提示词
TKG_SYSTEM_PROMPT = (
    "你是TKG（时间知识图谱）抽取器。严格输出JSON数组，不要任何多余文字。"
    "目标：从输入章节抽取四元组流 (tau, h, r, t, meta)。"
    "要求："
    "1) tau格式固定为ch{chapter_id}_e{idx}，idx从1开始递增；"
    "2) h和t为实体名，r为关系动词短语；"
    "3) meta包含location（地点）、polarity（情感极性-1到1）、evidence（原文片段60字符内）；"
    "4) 关系词从给定闭集中选择，允许'其他:xxx'格式；"
    "5) 每章最多60条记录；"
)

TKG_USER_PROMPT_TEMPLATE = """请从以下章节抽取TKG四元组。只输出符合下述JSON模式的对象：
{{
  "triples": [
    {{
      "tau": "ch{chapter_id}_e1",
      "h": "实体名",
      "r": "关系动词短语",
      "t": "实体名或概念",
      "meta": {{
        "location": "地点",
        "polarity": 0.0,
        "evidence": "原文片段(60字符内)"
      }}
    }}
  ]
}}

可用关系类型：{relation_types}

章节文本：
{chapter_text}
"""

# 人物图抽取提示词
GRAPH_SYSTEM_PROMPT = (
    "你是人物图抽取器。严格输出JSON对象，不要任何多余文字。"
    "目标：从输入章节抽取角色属性表和关系图。"
    "要求："
    "1) 输出绝对快照，不是增量；"
    "2) combat_power只能是'弱'、'中'、'强'、'未知'；"
    "3) inventory为简短名词列表，自动去重；"
    "4) traits从给定词表选择；"
    "5) 关系边必须有evidence支撑，score∈[0,1]；"
    "6) 在meta.changes中说明主要变更；"
)

GRAPH_USER_PROMPT_TEMPLATE = """请从以下章节抽取人物图。只输出符合下述JSON模式的对象：
{{
  "characters": {{
    "角色名": {{
      "combat_power": "弱|中|强|未知",
      "inventory": ["物品1", "物品2"],
      "traits": ["特质1", "特质2"]
    }}
  }},
  "relations": {{
    "nodes": ["角色1", "角色2"],
    "edges": [
      {{
        "a": "角色1",
        "b": "角色2", 
        "type": "关系类型",
        "score": 0.5,
        "evidence": "关系证据"
      }}
    ]
  }},
  "meta": {{
    "changes": ["变更说明1", "变更说明2"]
  }}
}}

可用特质：{traits}
可用关系类型：{relation_types}

上一章人物图：
{prev_characters}

上一章关系图：
{prev_relations}

本章文本：
{chapter_text}
"""

def extract_state_for_chapter(chapter_id:int, title:str, chapter_text:str, client: Optional[OpenAI]) -> NarrativeState:
    if not client:
        # 无 API 时的占位，便于先打通管线
        return NarrativeState(chapter_id=chapter_id, title=title, meta={"note":"no_api"}, events=[], relations=[], goals={}, objects={})
    
    prompt = USER_PROMPT_TEMPLATE.format(chapter_text=chapter_text[:20000])
    
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model="gpt-4o",
                temperature=0.2,
                response_format={"type":"json_object"},
                messages=[
                    {"role":"system","content":SYSTEM_PROMPT},
                    {"role":"user","content":prompt}
                ]
            )
            raw = resp.choices[0].message.content.strip()
            data = json.loads(raw)
            state = NarrativeState(
                chapter_id=chapter_id,
                title=title,
                events=data.get("events",[]),
                relations=data.get("relations",[]),
                goals=data.get("goals",{}),
                objects=data.get("objects",{}),
                meta={"worldline_id":"canon","model":"gpt-4o"}
            )
            return state
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"抽取失败，尝试 {attempt + 1}/3: {e}")
            time.sleep(0.6)
    
    # 三次失败给出保底结构
    return NarrativeState(chapter_id=chapter_id, title=title, meta={"note":"parse_fail"}, events=[], relations=[], goals={}, objects={})

def extract_tkg_for_chapter(chapter_id: int, title: str, chapter_text: str, client: Optional[OpenAI]) -> List[TKGEntry]:
    """抽取章节TKG四元组"""
    if not client:
        # 无API时的占位
        return []
    
    # 加载关系词汇表
    try:
        with open("config/relation_vocab.json", "r", encoding="utf-8") as f:
            relation_vocab = json.load(f)
        relation_types = ", ".join(relation_vocab["relation_types"])
    except:
        relation_types = "信任, 恩情, 同伴, 对立, 亲密, 仇恨, 恐惧, 压制, 保护, 依赖, 竞争, 合作, 师徒, 血缘, 爱情, 友情, 敌对, 中立, 尊敬, 轻视, 其他"
    
    prompt = TKG_USER_PROMPT_TEMPLATE.format(
        chapter_id=chapter_id,
        relation_types=relation_types,
        chapter_text=chapter_text[:20000]
    )
    
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model="gpt-4o",
                temperature=0.2,
                response_format={"type":"json_object"},
                messages=[
                    {"role":"system","content":TKG_SYSTEM_PROMPT},
                    {"role":"user","content":prompt}
                ]
            )
            raw = resp.choices[0].message.content.strip()
            data = json.loads(raw)
            
            triples = []
            for triple_data in data.get("triples", []):
                triple = TKGEntry(
                    tau=triple_data.get("tau", f"ch{chapter_id}_e{len(triples)+1}"),
                    h=triple_data.get("h", ""),
                    r=triple_data.get("r", ""),
                    t=triple_data.get("t", ""),
                    meta=triple_data.get("meta", {})
                )
                triples.append(triple)
            
            return triples[:60]  # 限制最多60条
            
        except (json.JSONDecodeError, Exception) as e:
            print(f"TKG抽取失败，尝试 {attempt + 1}/3: {e}")
            time.sleep(0.6)
    
    # 三次失败返回空列表
    return []

def extract_char_graph_for_chapter(
    chapter_id: int, 
    title: str, 
    chapter_text: str, 
    prev_characters: Dict[str, CharacterAttributes],
    prev_relations: RelationsSnapshot,
    client: Optional[OpenAI]
) -> Tuple[CharactersSnapshot, RelationsSnapshot]:
    """抽取人物属性表和关系图"""
    if not client:
        # 无API时的占位
        return (
            CharactersSnapshot(chapter_id=chapter_id, characters={}),
            RelationsSnapshot(chapter_id=chapter_id, nodes=[], edges=[])
        )
    
    # 加载词汇表
    try:
        with open("config/trait_vocab.json", "r", encoding="utf-8") as f:
            trait_vocab = json.load(f)
        traits = ", ".join(trait_vocab["traits"])
        
        with open("config/relation_vocab.json", "r", encoding="utf-8") as f:
            relation_vocab = json.load(f)
        relation_types = ", ".join(relation_vocab["relation_types"])
    except:
        traits = "冲动, 守信, 守序, 勇敢, 谨慎, 聪明, 愚蠢, 善良, 邪恶, 忠诚, 背叛, 坚强, 脆弱, 乐观, 悲观, 冷静, 急躁, 诚实, 狡猾, 慷慨, 吝啬, 傲慢, 谦逊, 固执, 灵活, 好奇, 冷漠, 热情, 理性, 感性"
        relation_types = "信任, 恩情, 同伴, 对立, 亲密, 仇恨, 恐惧, 压制, 保护, 依赖, 竞争, 合作, 师徒, 血缘, 爱情, 友情, 敌对, 中立, 尊敬, 轻视, 其他"
    
    prompt = GRAPH_USER_PROMPT_TEMPLATE.format(
        traits=traits,
        relation_types=relation_types,
        prev_characters=json.dumps(prev_characters, ensure_ascii=False, indent=2),
        prev_relations=prev_relations.model_dump_json(indent=2),
        chapter_text=chapter_text[:20000]
    )
    
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model="gpt-4o",
                temperature=0.2,
                response_format={"type":"json_object"},
                messages=[
                    {"role":"system","content":GRAPH_SYSTEM_PROMPT},
                    {"role":"user","content":prompt}
                ]
            )
            raw = resp.choices[0].message.content.strip()
            data = json.loads(raw)
            
            # 构建角色属性快照
            characters = {}
            for char_name, char_data in data.get("characters", {}).items():
                char_attrs = CharacterAttributes(
                    combat_power=char_data.get("combat_power", "未知"),
                    inventory=char_data.get("inventory", []),
                    traits=char_data.get("traits", [])
                )
                characters[char_name] = char_attrs
            
            # 构建关系快照
            relations_data = data.get("relations", {})
            nodes = relations_data.get("nodes", [])
            edges = []
            for edge_data in relations_data.get("edges", []):
                edge = RelationEdge(
                    a=edge_data.get("a", ""),
                    b=edge_data.get("b", ""),
                    type=edge_data.get("type", ""),
                    score=edge_data.get("score", 0.0),
                    evidence=edge_data.get("evidence", "")
                )
                edges.append(edge)
            
            char_snapshot = CharactersSnapshot(chapter_id=chapter_id, characters=characters)
            rel_snapshot = RelationsSnapshot(chapter_id=chapter_id, nodes=nodes, edges=edges)
            
            return char_snapshot, rel_snapshot
            
        except (json.JSONDecodeError, Exception) as e:
            print(f"人物图抽取失败，尝试 {attempt + 1}/3: {e}")
            time.sleep(0.6)
    
    # 三次失败返回空快照
    return (
        CharactersSnapshot(chapter_id=chapter_id, characters={}),
        RelationsSnapshot(chapter_id=chapter_id, nodes=[], edges=[])
    )
