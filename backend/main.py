#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后端API服务器 - 多智能体故事世界系统
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import os
import sys
import json
from openai import OpenAI

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agent_system import AgentSystem, CharacterAgent
from world_engine import WorldEngine
from data_loader import DataLoader
from memory_system import MemorySystem
from emotion_system import EmotionSystem, EmotionType
from motivation_system import MotivationSystem, Motivation, MotivationLevel, MotivationPriority, MotivationStatus
from npc_generator import NPCGenerator, NPC, NPCRole
from world_manager import WorldManager, World
from knowledge_base import NovelKnowledgeBase

app = FastAPI(title="多智能体故事世界API", version="1.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局系统实例
agent_system: Optional[AgentSystem] = None
world_engine: Optional[WorldEngine] = None
data_loader: Optional[DataLoader] = None
memory_system: Optional[MemorySystem] = None
emotion_system: Optional[EmotionSystem] = None
motivation_system: Optional[MotivationSystem] = None
npc_generator: Optional[NPCGenerator] = None
world_manager: Optional[WorldManager] = None
knowledge_base: Optional[NovelKnowledgeBase] = None
current_world_id: Optional[str] = None

# 初始化LLM客户端（使用SiliconFlow的Qwen模型）
def get_openai_client():
    from config import get_api_key, SILICONFLOW_BASE_URL
    api_key = get_api_key()
    if not api_key:
        print("⚠️  未找到API Key，请设置 SILICONFLOW_API_KEY 或 OPENAI_API_KEY 环境变量")
        return None
    # SiliconFlow兼容OpenAI格式，使用Qwen/Qwen2.5-7B-Instruct模型
    try:
        client = OpenAI(
            api_key=api_key,
            base_url=SILICONFLOW_BASE_URL
        )
        print(f"✅ 已连接到 SiliconFlow API: {SILICONFLOW_BASE_URL}")
        return client
    except Exception as e:
        print(f"❌ 初始化LLM客户端失败: {e}")
        return None

# ==================== 请求/响应模型 ====================

class WorldInitRequest(BaseModel):
    """初始化世界请求"""
    novel_file: Optional[str] = None
    worldline_id: str = "canon"

class CharacterActionRequest(BaseModel):
    """角色行动请求"""
    character_name: str
    action_type: str  # "plan", "dialogue", "act"
    target: Optional[str] = None
    context: Optional[str] = None

class WorldAdvanceRequest(BaseModel):
    """世界推进请求"""
    time_step: int = 1
    focus_characters: Optional[List[str]] = None
    auto_save: bool = True  # 是否自动保存

class DialogueRequest(BaseModel):
    """对话请求"""
    speaker: str
    listener: str
    topic: Optional[str] = None
    context: Optional[str] = None

class EventGenerationRequest(BaseModel):
    """事件生成请求"""
    location: Optional[str] = None
    participants: Optional[List[str]] = None
    event_type: Optional[str] = None

class StoryContinueRequest(BaseModel):
    """自动续写故事请求"""
    history: str  # 之前已经写出的故事正文（可以是最近一段）
    recent_events: List[Dict[str, Any]] = []  # 最近的事件时间线片段

class CharacterUpdateRequest(BaseModel):
    """角色属性更新请求"""
    location: Optional[str] = None
    status: Optional[str] = None
    goals: Optional[List[str]] = None
    inventory: Optional[List[str]] = None
    combat_power: Optional[str] = None
    traits: Optional[List[str]] = None

class MemoryAddRequest(BaseModel):
    """添加记忆请求"""
    character_name: str
    content: str
    memory_type: str  # "dialogue", "event", "action", "observation"
    metadata: Optional[Dict[str, Any]] = None

class MemorySearchRequest(BaseModel):
    """检索记忆请求"""
    query: str
    top_k: Optional[int] = 5
    memory_types: Optional[List[str]] = None
    min_similarity: Optional[float] = 0.3

class EmotionDecayRequest(BaseModel):
    """情感衰减请求"""
    character_name: str
    decay_factor: Optional[float] = 0.1

class MotivationAddRequest(BaseModel):
    """添加动机请求"""
    character_name: str
    description: str
    level: str  # "短期", "中期", "长期"
    priority: Optional[str] = "一般"  # "紧急", "重要", "一般", "较低"
    depending_on: Optional[str] = None  # 依赖的其他动机ID

class MotivationUpdateRequest(BaseModel):
    """更新动机请求"""
    progress: Optional[float] = None
    status: Optional[str] = None
    note: Optional[str] = None

class MotivationBlockerRequest(BaseModel):
    """添加阻碍因素请求"""
    blocker: str

class NPCGenerateRequest(BaseModel):
    """生成NPC请求"""
    role: Optional[str] = None  # 角色类型，None则随机
    location: str = "乡村"  # 所在地点
    gender: str = "random"  # 性别：male/female/random

class NPCBatchGenerateRequest(BaseModel):
    """批量生成NPC请求"""
    count: int = 5  # 生成的NPC数量
    location: str = "乡村"  # 所在地点
    allowed_roles: Optional[List[str]] = None  # 允许的角色类型

class CreateWorldRequest(BaseModel):
    """创建世界请求"""
    name: str
    description: str = ""
    template: Optional[str] = None  # "canon", "user_branch", or None

class UpdateWorldRequest(BaseModel):
    """更新世界请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class LoadWorldRequest(BaseModel):
    """加载世界请求"""
    world_id: str

class ImportWorldRequest(BaseModel):
    """导入世界请求"""
    name: str
    description: str = ""

class NovelImportRequest(BaseModel):
    """导入小说文本请求"""
    text: str
    novel_name: str = "未命名小说"

class KnowledgeQueryRequest(BaseModel):
    """知识库查询请求"""
    query: str
    context_type: str = "all"  # "all", "character", "location", "event", "scene"
    top_k: int = 5

# ==================== 辅助函数 ====================

async def auto_save_current_world() -> bool:
    """自动保存当前世界状态"""
    if not world_manager or not current_world_id:
        return False
    
    try:
        world_state = {
            "time": world_engine.current_time,
            "locations": world_engine.locations,
            "recent_events": world_engine.recent_events,
            "characters": {}
        }
        
        # 收集所有角色数据
        if agent_system:
            for name, agent in agent_system.agents.items():
                chars = world_state["characters"]
                chars[name] = {
                    "attributes": agent.attributes.model_dump() if agent.attributes else {},
                    "location": agent.location,
                    "status": agent.status,
                    "goals": agent.goals,
                    "inventory": agent.inventory,
                    "relations": agent.relations
                }
        
        # 保存情感和动机状态到世界状态中
        if emotion_system:
            world_state["emotions"] = emotion_system.to_dict()
        
        if motivation_system:
            world_state["motivations"] = motivation_system.to_dict()
        
        # 保存完整的世界状态
        world_manager.save_world_state(current_world_id, world_state)
        
        print(f"💾 世界状态已自动保存: {current_world_id}")
        return True
    except Exception as e:
        print(f"⚠️ 自动保存失败: {e}")
        return False

# ==================== API端点 ====================

def initialize_default_motivations():
    """为角色初始化默认动机数据"""
    from motivation_system import Motivation, MotivationLevel, MotivationPriority, MotivationStatus
    
    # 银发少女的动机
    motivation_system.add_motivation("银发少女", Motivation(
        description="探索这个世界的秘密，寻找回到故乡的方法",
        level=MotivationLevel.LONG_TERM,
        priority=MotivationPriority.HIGH,
        status=MotivationStatus.IN_PROGRESS,
        progress=0.2
    ))
    motivation_system.add_motivation("银发少女", Motivation(
        description="阻止即将到来的灾难，守护这个世界",
        level=MotivationLevel.LONG_TERM,
        priority=MotivationPriority.CRITICAL,
        status=MotivationStatus.IN_PROGRESS,
        progress=0.1
    ))
    motivation_system.add_motivation("银发少女", Motivation(
        description="与旅行者建立互信关系",
        level=MotivationLevel.MEDIUM_TERM,
        priority=MotivationPriority.HIGH,
        status=MotivationStatus.IN_PROGRESS,
        progress=0.5
    ))
    motivation_system.add_motivation("银发少女", Motivation(
        description="与村长交流，获取更多信息",
        level=MotivationLevel.SHORT_TERM,
        priority=MotivationPriority.HIGH,
        status=MotivationStatus.IN_PROGRESS,
        progress=0.6
    ))
    
    # 旅行者的动机
    motivation_system.add_motivation("旅行者", Motivation(
        description="揭开这个世界的真相",
        level=MotivationLevel.LONG_TERM,
        priority=MotivationPriority.NORMAL,
        status=MotivationStatus.IN_PROGRESS,
        progress=0.15
    ))
    motivation_system.add_motivation("旅行者", Motivation(
        description="提升自己的能力，保护同伴",
        level=MotivationLevel.MEDIUM_TERM,
        priority=MotivationPriority.HIGH,
        status=MotivationStatus.IN_PROGRESS,
        progress=0.4
    ))
    motivation_system.add_motivation("旅行者", Motivation(
        description="与银发少女建立友好关系",
        level=MotivationLevel.SHORT_TERM,
        priority=MotivationPriority.HIGH,
        status=MotivationStatus.IN_PROGRESS,
        progress=0.7
    ))
    
    # 村长的动机
    motivation_system.add_motivation("村长", Motivation(
        description="守护村子的安宁，保护村民",
        level=MotivationLevel.LONG_TERM,
        priority=MotivationPriority.HIGH,
        status=MotivationStatus.IN_PROGRESS,
        progress=0.6
    ))
    motivation_system.add_motivation("村长", Motivation(
        description="帮助银发少女和旅行者",
        level=MotivationLevel.MEDIUM_TERM,
        priority=MotivationPriority.NORMAL,
        status=MotivationStatus.IN_PROGRESS,
        progress=0.5
    ))
    motivation_system.add_motivation("村长", Motivation(
        description="处理村子的日常事务",
        level=MotivationLevel.SHORT_TERM,
        priority=MotivationPriority.NORMAL,
        status=MotivationStatus.IN_PROGRESS,
        progress=0.8
    ))
    
    # 商人的动机
    motivation_system.add_motivation("商人", Motivation(
        description="扩大生意，建立贸易网络",
        level=MotivationLevel.LONG_TERM,
        priority=MotivationPriority.NORMAL,
        status=MotivationStatus.IN_PROGRESS,
        progress=0.3
    ))
    motivation_system.add_motivation("商人", Motivation(
        description="向旅行者推销商品",
        level=MotivationLevel.SHORT_TERM,
        priority=MotivationPriority.HIGH,
        status=MotivationStatus.PENDING,
        progress=0.0
    ))
    
    print("✅ 默认动机数据已加载")


@app.on_event("startup")
async def startup_event():
    """启动时初始化系统"""
    global agent_system, world_engine, data_loader, memory_system, emotion_system, motivation_system, npc_generator, world_manager, knowledge_base, current_world_id
    client = get_openai_client()
    
    # 检查API key配置
    from config import get_api_key, is_api_configured, DEFAULT_API_KEY
    api_key = get_api_key()
    if api_key == DEFAULT_API_KEY:
        print(f"✅ 使用默认API Key: {api_key[:10]}...")
    elif is_api_configured():
        print(f"✅ 使用环境变量API Key: {api_key[:10]}...")
    else:
        print("⚠️  警告: 未检测到API Key，LLM功能将不可用")
    
    if client:
        print("✅ LLM客户端初始化成功")
    else:
        print("❌ LLM客户端初始化失败（API Key未配置）")
    
    data_loader = DataLoader()
    
    # 初始化记忆系统
    memory_system = MemorySystem()
    memory_system.load_from_disk()
    print("✅ 记忆系统初始化完成")
    
    # 初始化情感系统
    emotion_system = EmotionSystem()
    print("✅ 情感系统初始化完成")
    
    # 初始化动机系统
    motivation_system = MotivationSystem()
    print("✅ 动机系统初始化完成")
    
    # 加载默认动机数据
    initialize_default_motivations()
    
    # 初始化NPC生成器
    npc_generator = NPCGenerator()
    print("✅ NPC生成器初始化完成")
    
    agent_system = AgentSystem(client, memory_system, emotion_system, motivation_system)
    world_engine = WorldEngine(client, agent_system, emotion_system, motivation_system, npc_generator)
    
    # 初始化世界管理器
    try:
        world_manager = WorldManager()
        print("✅ 世界管理器初始化完成")
        print(f"   世界存储目录: {world_manager.storage_dir}")
        print(f"   已加载 {len(world_manager.list_worlds())} 个世界")
    except Exception as e:
        print(f"❌ 世界管理器初始化失败: {e}")
        import traceback
        traceback.print_exc()
        world_manager = None
    
    # 初始化知识库（传入LLM客户端以支持AI智能提取）
    try:
        if client:
            knowledge_base = NovelKnowledgeBase(llm_client=client)
            print("✅ 知识库系统初始化完成（AI增强模式）")
        else:
            knowledge_base = NovelKnowledgeBase()
            print("✅ 知识库系统初始化完成（基础模式 - 无AI功能）")
            print("   提示：配置API Key后可启用AI智能提取功能")
    except Exception as e:
        print(f"❌ 知识库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        knowledge_base = None
    
    print("✅ 系统初始化完成")

@app.get("/")
async def root():
    """根端点"""
    return {"message": "多智能体故事世界API", "status": "running"}

@app.post("/api/world/init")
async def init_world(request: WorldInitRequest):
    """初始化世界"""
    try:
        if not data_loader:
            raise HTTPException(status_code=500, detail="数据加载器未初始化")
        
        # 加载世界数据
        world_data = data_loader.load_world_data(request.worldline_id)
        
        # 初始化智能体系统
        if agent_system:
            agent_system.initialize_agents(world_data)
        
        # 初始化世界引擎
        if world_engine:
            world_engine.initialize(world_data)
        
        return {
            "status": "success",
            "world_data": world_data,
            "characters": list(agent_system.agents.keys()) if agent_system else []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/world/state")
async def get_world_state():
    """获取当前世界状态"""
    if not world_engine:
        raise HTTPException(status_code=500, detail="世界引擎未初始化")
    
    return {
        "current_time": world_engine.current_time,
        "locations": world_engine.locations,
        "characters": {
            name: {
                "location": agent.location,
                "status": agent.status,
                "goals": agent.goals
            }
            for name, agent in agent_system.agents.items()
        } if agent_system else {},
        "recent_events": world_engine.recent_events[-10:]
    }

@app.get("/api/characters")
async def get_characters():
    """获取所有角色信息"""
    if not agent_system:
        raise HTTPException(status_code=500, detail="智能体系统未初始化")
    
    characters = []
    for name, agent in agent_system.agents.items():
        # 获取情感状态
        emotion_state = None
        if emotion_system:
            state = emotion_system.get_emotion_state(name)
            if state:
                emotion_state = state.to_dict()
        
        # 获取动机汇总
        motivation_summary = None
        if motivation_system:
            motivation_summary = motivation_system.get_motivation_summary(name)
        
        characters.append({
            "name": name,
            "attributes": agent.attributes.model_dump() if agent.attributes else {},
            "location": agent.location,
            "status": agent.status,
            "goals": agent.goals,
            "inventory": agent.inventory,
            "emotions": emotion_state,
            "motivations": motivation_summary
        })
    
    return {"characters": characters}

@app.get("/api/characters/{character_name}")
async def get_character(character_name: str):
    """获取特定角色信息"""
    if not agent_system:
        raise HTTPException(status_code=500, detail="智能体系统未初始化")
    
    if character_name not in agent_system.agents:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    agent = agent_system.agents[character_name]
    
    # 获取情感状态
    emotion_state = None
    if emotion_system:
        state = emotion_system.get_emotion_state(character_name)
        if state:
            emotion_state = state.to_dict()
    
    # 获取动机汇总
    motivation_summary = None
    if motivation_system:
        motivation_summary = motivation_system.get_motivation_summary(character_name)
    
    return {
        "name": character_name,
        "attributes": agent.attributes.model_dump() if agent.attributes else {},
        "location": agent.location,
        "status": agent.status,
        "goals": agent.goals,
        "inventory": agent.inventory,
        "relations": agent.relations,
        "emotions": emotion_state,
        "motivations": motivation_summary
    }

@app.post("/api/characters/{character_name}/plan")
async def character_plan(character_name: str):
    """角色制定计划"""
    if not agent_system:
        raise HTTPException(status_code=500, detail="智能体系统未初始化")
    
    if character_name not in agent_system.agents:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    agent = agent_system.agents[character_name]
    plan = await agent.generate_plan(world_engine.get_world_context() if world_engine else {})
    
    return {
        "character": character_name,
        "plan": plan
    }

@app.put("/api/characters/{character_name}")
async def update_character(character_name: str, request: CharacterUpdateRequest):
    """更新角色属性"""
    if not agent_system:
        raise HTTPException(status_code=500, detail="智能体系统未初始化")
    
    if character_name not in agent_system.agents:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    agent = agent_system.agents[character_name]
    
    # 更新动态属性
    if request.location is not None:
        agent.location = request.location
    if request.status is not None:
        agent.status = request.status
    if request.goals is not None:
        agent.goals = request.goals
    if request.inventory is not None:
        agent.inventory = request.inventory
    
    # 更新静态属性（需要修改CharacterAttributes对象）
    if request.combat_power is not None or request.traits is not None:
        from tkg_models import CombatPower
        if agent.attributes:
            if request.combat_power is not None:
                try:
                    agent.attributes.combat_power = CombatPower(request.combat_power)
                except ValueError:
                    pass  # 如果值无效，保持原值
            if request.traits is not None:
                agent.attributes.traits = request.traits
    
    # 自动保存
    await auto_save_current_world()
    
    return {
        "status": "success",
        "character": character_name,
        "updated_attributes": {
            "location": agent.location,
            "status": agent.status,
            "goals": agent.goals,
            "inventory": agent.inventory,
            "attributes": agent.attributes.model_dump() if agent.attributes else {}
        }
    }

@app.post("/api/dialogue")
async def generate_dialogue(request: DialogueRequest):
    """生成角色对话"""
    if not agent_system:
        raise HTTPException(status_code=500, detail="智能体系统未初始化")
    
    if request.speaker not in agent_system.agents:
        raise HTTPException(status_code=404, detail=f"角色 {request.speaker} 不存在")
    if request.listener not in agent_system.agents:
        raise HTTPException(status_code=404, detail=f"角色 {request.listener} 不存在")
    
    speaker_agent = agent_system.agents[request.speaker]
    listener_agent = agent_system.agents[request.listener]
    
    # 检查客户端是否可用
    if not speaker_agent.client:
        from config import is_api_configured
        if not is_api_configured():
            raise HTTPException(
                status_code=503, 
                detail="LLM服务不可用：未配置API Key。请设置 SILICONFLOW_API_KEY 或 OPENAI_API_KEY 环境变量"
            )
        else:
            raise HTTPException(
                status_code=503,
                detail="LLM客户端未初始化，请检查后端日志"
            )
    
    dialogue = await speaker_agent.generate_dialogue(
        listener_agent,
        request.topic,
        request.context
    )
    
    # 自动保存对话记忆
    if memory_system and "content" in dialogue:
        memory_system.add_memory(
            character_name=request.speaker,
            content=f"我对 {request.listener} 说：{dialogue['content']}",
            memory_type="dialogue",
            metadata={
                "listener": request.listener,
                "topic": request.topic,
                "context": request.context,
                "tone": dialogue.get("tone", ""),
                "intent": dialogue.get("intent", "")
            }
        )
    
    # 处理说话者的情感触发
    emotion_changes = []
    if emotion_system and "content" in dialogue:
        # 分析对话内容，触发情感变化
        change1 = emotion_system.process_trigger(
            character_name=request.speaker,
            trigger_type="dialogue",
            content=dialogue['content'],
            metadata={"listener": request.listener, "topic": request.topic}
        )
        if change1.get("changed"):
            emotion_changes.append(change1)
        
        # 如果对话内容涉及倾听者，也可能影响倾听者的情感
        if request.listener in dialogue['content']:
            change2 = emotion_system.process_trigger(
                character_name=request.listener,
                trigger_type="dialogue",
                content=dialogue['content'],
                metadata={"speaker": request.speaker, "topic": request.topic}
            )
            if change2.get("changed"):
                emotion_changes.append(change2)
    
    return {
        "speaker": request.speaker,
        "listener": request.listener,
        "dialogue": dialogue,
        "emotion_changes": emotion_changes
    }

@app.post("/api/world/advance")
async def advance_world(request: WorldAdvanceRequest):
    """推进世界时间"""
    if not world_engine:
        raise HTTPException(status_code=500, detail="世界引擎未初始化")
    
    events = await world_engine.advance(
        time_steps=request.time_step,
        focus_characters=request.focus_characters
    )
    
    # 自动保存世界状态
    saved = False
    if request.auto_save and world_manager and current_world_id:
        try:
            world_state = {
                "time": world_engine.current_time,
                "locations": world_engine.locations,
                "recent_events": world_engine.recent_events,
                "characters": {}
            }
            
            # 收集所有角色数据
            if agent_system:
                for name, agent in agent_system.agents.items():
                    chars = world_state["characters"]
                    chars[name] = {
                        "attributes": agent.attributes.model_dump() if agent.attributes else {},
                        "location": agent.location,
                        "status": agent.status,
                        "goals": agent.goals,
                        "inventory": agent.inventory,
                        "relations": agent.relations
                    }
            
            world_manager.save_world_state(current_world_id, world_state)
            
            # 保存情感和动机状态到世界状态中
            if emotion_system:
                world_state["emotions"] = emotion_system.to_dict()
            
            if motivation_system:
                world_state["motivations"] = motivation_system.to_dict()
            
            # 重新保存包含所有状态的数据
            world_manager.save_world_state(current_world_id, world_state)
            
            saved = True
            print(f"💾 世界状态已自动保存: {current_world_id}")
        except Exception as e:
            print(f"⚠️ 自动保存失败: {e}")
    
    return {
        "time_advanced": request.time_step,
        "new_events": events,
        "world_state": {
            "current_time": world_engine.current_time,
            "locations": world_engine.locations
        },
        "auto_saved": saved
    }

@app.post("/api/events/generate")
async def generate_event(request: EventGenerationRequest):
    """生成事件"""
    if not world_engine:
        raise HTTPException(status_code=500, detail="世界引擎未初始化")
    
    event = await world_engine.generate_event(
        location=request.location,
        participants=request.participants,
        event_type=request.event_type
    )
    
    # 自动保存事件记忆给所有参与者
    if memory_system and request.participants:
        event_desc = f"在 {event.get('location', '未知地点')} 发生了 {event.get('type', '事件')}"
        if event.get('description'):
            event_desc += f"：{event['description']}"
        
        for participant in request.participants:
            memory_system.add_memory(
                character_name=participant,
                content=event_desc,
                memory_type="event",
                metadata={
                    "location": event.get('location'),
                    "event_type": event.get('type'),
                    "time": event.get('time'),
                    "participants": request.participants
                }
            )
    
    # 处理参与者的情感触发
    emotion_changes = []
    if emotion_system and request.participants:
        event_desc_full = event.get('description', event.get('title', ''))
        for participant in request.participants:
            change = emotion_system.process_trigger(
                character_name=participant,
                trigger_type="event",
                content=event_desc_full,
                metadata={
                    "location": request.location,
                    "event_type": request.event_type,
                    "participants": request.participants
                }
            )
            if change.get("changed"):
                emotion_changes.append(change)
    
    return {
        "event": event,
        "emotion_changes": emotion_changes
    }

@app.post("/api/story/continue")
async def continue_story(request: StoryContinueRequest):
    """根据最近事件和既有正文，自动续写一小段小说"""
    client = get_openai_client()
    if not client:
        raise HTTPException(status_code=503, detail="LLM客户端未初始化，无法续写故事")

    # 整理最近事件，压缩为简要提纲
    recent_events = request.recent_events[-6:] if request.recent_events else []
    events_summary_lines = []
    for ev in recent_events:
        t = ev.get("time", "?")
        loc = ev.get("location", "未知地点")
        title = ev.get("title") or ev.get("type") or "事件"
        desc = ev.get("description", "")
        events_summary_lines.append(f"· 时间{t}，地点「{loc}」，{title}：{desc[:80]}")
    events_summary = "\n".join(events_summary_lines) if events_summary_lines else "（暂无明确事件提纲，可根据既有正文自然推进。）"

    # 为避免 prompt 过长，只保留历史正文的末尾一段
    history_tail = request.history[-4000:] if request.history else ""

    # 收集参与角色的情感、动机和记忆信息
    characters_context = ""
    if agent_system and (emotion_system or motivation_system or memory_system):
        for name, agent in agent_system.agents.items():
            char_context = f"\n【{name}】\n"
            
            # 添加情感状态
            if emotion_system:
                emotion_state = emotion_system.get_emotion_state(name)
                if emotion_state:
                    emotion_list = []
                    emotion_list.append(f"{emotion_state.primary_emotion.value}({emotion_state.intensity:.1f})")
                    if emotion_state.secondary_emotion != EmotionType.NEUTRAL:
                        emotion_list.append(f"{emotion_state.secondary_emotion.value}({emotion_state.secondary_intensity:.1f})")
                    char_context += f"当前情感：{', '.join(emotion_list)}\n"
            
            # 添加动机信息
            if motivation_system:
                active_mots = motivation_system.get_active_motivations(name, include_blocked=True)
                if active_mots:
                    char_context += "主要目标：\n"
                    for m in active_mots[:3]:  # 只取前3个活跃动机
                        priority_text = {
                            MotivationPriority.CRITICAL: "【紧急】",
                            MotivationPriority.HIGH: "【重要】",
                            MotivationPriority.NORMAL: "【一般】",
                            MotivationPriority.LOW: "【较低】"
                        }.get(m.priority, "")
                        level_text = {
                            MotivationLevel.SHORT_TERM: "短期",
                            MotivationLevel.MEDIUM_TERM: "中期",
                            MotivationLevel.LONG_TERM: "长期"
                        }.get(m.level, "")
                        char_context += f"  {priority_text}{level_text}：{m.description}（进度{m.progress*100:.0f}%）\n"
            
            # 添加相关记忆
            if memory_system and recent_events:
                # 从最近事件中提取角色名，查找相关记忆
                relevant_memories = []
                # 检索最近3条事件的描述作为查询
                query_texts = [ev.get("description", "") for ev in recent_events[-3:]]
                # 获取与这些事件相关的记忆
                for query in query_texts:
                    if query:
                        memories = memory_system.retrieve_memories(name, query, top_k=2)
                        for mem in memories:
                            if mem not in relevant_memories:
                                relevant_memories.append(mem)
                
                if relevant_memories:
                    char_context += "相关记忆：\n"
                    for i, mem in enumerate(relevant_memories[:5], 1):  # 最多5条相关记忆
                        char_context += f"  {i}. {mem.content}\n"
            
            characters_context += char_context

    system_prompt = (
        "你是一名擅长长篇连续叙事的小说作者，负责将事件时间线转化为自然流畅的小说正文。\n"
        "要求：\n"
        "1. 只输出中文小说正文，不要说明、不要列表、不要 JSON。\n"
        "2. 续写应与已有正文无缝衔接，保持人物性格和世界观连贯。\n"
        "3. 每次续写控制在大约 300～800 字，形成 1～3 个自然段即可。\n"
        "4. 可以包含对话，但整体以叙事为主，让读者感觉是在读小说，不是看提纲。\n"
        "5. 不要重复逐字复述事件提纲，用自己的语言演绎这些事件。\n"
        "6. 特别注意角色的情感状态和动机，在小说中体现其内心感受和目标追求。\n"
        "7. 可以通过内心独白、行为微表情等方式展现角色的心理状态。\n"
        "8. 角色的行动应该与其当前的动机相呼应，展现其为目标付出的努力。\n"
    )

    user_content = f"""【已有小说正文（节选，供你参考，不要重复照抄）】
{history_tail}

【最近的事件提纲】
{events_summary}
{characters_context}
【续写任务】
请在以上正文的基础上，继续往后写一小段完整小说内容。保持人物行为和情绪合理，延续剧情发展。注意融入角色的情感状态和内在动机，使故事更加立体丰满。
"""

    try:
        resp = client.chat.completions.create(
            model="Qwen/Qwen2.5-7B-Instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.85,
            max_tokens=800,
        )
        text = resp.choices[0].message.content.strip()
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"故事续写失败: {e}")

@app.get("/api/locations")
async def get_locations():
    """获取所有地点信息"""
    if not world_engine:
        raise HTTPException(status_code=500, detail="世界引擎未初始化")
    
    return {
        "locations": world_engine.locations,
        "location_map": world_engine.location_map
    }

@app.get("/api/relations")
async def get_relations():
    """获取角色关系图"""
    if not agent_system:
        raise HTTPException(status_code=500, detail="智能体系统未初始化")
    
    relations = []
    for name, agent in agent_system.agents.items():
        for rel in agent.relations:
            relations.append({
                "from": name,
                "to": rel.get("target", ""),
                "type": rel.get("type", ""),
                "score": rel.get("score", 0.0)
            })
    
    return {"relations": relations}

# ==================== NPC生成系统 API ====================

@app.get("/api/npc/roles")
async def get_npc_roles():
    """获取所有可用的NPC角色类型"""
    return {
        "roles": [role.value for role in NPCRole]
    }

@app.post("/api/npc/generate")
async def generate_npc(request: NPCGenerateRequest):
    """生成单个NPC"""
    if not npc_generator:
        raise HTTPException(status_code=500, detail="NPC生成器未初始化")
    
    # 解析角色类型
    role = None
    if request.role:
        try:
            # 尝试从值查找对应的枚举
            role = NPCRole(request.role)
        except ValueError:
            # 如果找不到，使用随机
            role = None
    
    # 生成NPC
    npc = npc_generator.generate_npc(
        role=role,
        location=request.location,
        gender=request.gender
    )
    
    return npc.to_dict()

@app.post("/api/npc/generate-batch")
async def generate_npc_batch(request: NPCBatchGenerateRequest):
    """批量生成NPC"""
    if not npc_generator:
        raise HTTPException(status_code=500, detail="NPC生成器未初始化")
    
    # 解析允许的角色类型
    allowed_roles = None
    if request.allowed_roles:
        allowed_roles = []
        for role_str in request.allowed_roles:
            try:
                role = NPCRole(role_str)
                allowed_roles.append(role)
            except ValueError:
                continue
        
        if not allowed_roles:
            allowed_roles = None
    
    # 批量生成NPC
    npcs = npc_generator.generate_npc_batch(
        count=request.count,
        location=request.location,
        allowed_roles=allowed_roles
    )
    
    return {
        "count": len(npcs),
        "npcs": [npc.to_dict() for npc in npcs]
    }

# ==================== 情感系统 API ====================

@app.get("/api/emotions/{character_name}")
async def get_character_emotions(character_name: str):
    """获取角色情感状态"""
    if not emotion_system:
        raise HTTPException(status_code=500, detail="情感系统未初始化")
    
    emotion_state = emotion_system.get_emotion_state(character_name)
    if not emotion_state:
        raise HTTPException(status_code=404, detail="角色情感状态不存在")
    
    return emotion_state.to_dict()

@app.get("/api/emotions")
async def get_all_emotions():
    """获取所有角色的情感状态"""
    if not emotion_system:
        raise HTTPException(status_code=500, detail="情感系统未初始化")
    
    return emotion_system.to_dict()

@app.post("/api/emotions/decay")
async def apply_emotion_decay(request: EmotionDecayRequest):
    """应用情感衰减"""
    if not emotion_system:
        raise HTTPException(status_code=500, detail="情感系统未初始化")
    
    result = emotion_system.apply_emotion_decay(
        character_name=request.character_name,
        decay_factor=request.decay_factor
    )
    
    return result

@app.post("/api/emotions/process-trigger")
async def process_emotion_trigger(
    character_name: str,
    trigger_type: str,
    content: str,
    metadata: Optional[Dict] = None
):
    """手动处理情感触发"""
    if not emotion_system:
        raise HTTPException(status_code=500, detail="情感系统未初始化")
    
    result = emotion_system.process_trigger(
        character_name=character_name,
        trigger_type=trigger_type,
        content=content,
        metadata=metadata
    )
    
    return result

# ==================== 动机系统 API ====================

@app.get("/api/motivations/{character_name}")
async def get_character_motivations(character_name: str):
    """获取角色动机状态"""
    if not motivation_system:
        raise HTTPException(status_code=500, detail="动机系统未初始化")
    
    motivation_system.initialize_character(character_name)
    summary = motivation_system.get_motivation_summary(character_name)
    
    return summary

@app.get("/api/motivations/{character_name}/level/{level}")
async def get_motivations_by_level(character_name: str, level: str):
    """按层级获取角色动机"""
    if not motivation_system:
        raise HTTPException(status_code=500, detail="动机系统未初始化")
    
    try:
        level_enum = MotivationLevel(level)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的层级: {level}")
    
    motivations = motivation_system.get_motivations_by_level(character_name, level_enum)
    return {
        "character_name": character_name,
        "level": level,
        "motivations": [m.to_dict() for m in motivations]
    }

@app.get("/api/motivations/{character_name}/active")
async def get_active_motivations(character_name: str, include_blocked: bool = False):
    """获取活跃动机"""
    if not motivation_system:
        raise HTTPException(status_code=500, detail="动机系统未初始化")
    
    active = motivation_system.get_active_motivations(character_name, include_blocked)
    return {
        "character_name": character_name,
        "active_motivations": [m.to_dict() for m in active]
    }

@app.post("/api/motivations/add")
async def add_motivation(request: MotivationAddRequest):
    """添加动机"""
    if not motivation_system:
        raise HTTPException(status_code=500, detail="动机系统未初始化")
    
    try:
        level_enum = MotivationLevel(request.level)
        priority_enum = MotivationPriority(request.priority)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"无效的参数: {e}")
    
    motivation = Motivation(
        description=request.description,
        level=level_enum,
        priority=priority_enum
    )
    
    motivation_id = motivation_system.add_motivation(
        character_name=request.character_name,
        motivation=motivation,
        depending_on=request.depending_on
    )
    
    return {
        "status": "success",
        "motivation_id": motivation_id,
        "message": "动机添加成功"
    }

@app.put("/api/motivations/{character_name}/{motivation_id}")
async def update_motivation(character_name: str, motivation_id: str, request: MotivationUpdateRequest):
    """更新动机"""
    if not motivation_system:
        raise HTTPException(status_code=500, detail="动机系统未初始化")
    
    # 更新进度
    if request.progress is not None:
        success = motivation_system.update_progress(
            character_name=character_name,
            motivation_id=motivation_id,
            progress=request.progress,
            note=request.note
        )
        if not success:
            raise HTTPException(status_code=404, detail="动机不存在")
    
    # 更新状态
    if request.status:
        try:
            status_enum = MotivationStatus(request.status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的状态: {request.status}")
        
        success = motivation_system.set_status(
            character_name=character_name,
            motivation_id=motivation_id,
            status=status_enum,
            note=request.note
        )
        if not success:
            raise HTTPException(status_code=404, detail="动机不存在")
    
    motivation = motivation_system.get_motivation(character_name, motivation_id)
    return {
        "status": "success",
        "message": "动机更新成功",
        "motivation": motivation.to_dict() if motivation else None
    }

@app.post("/api/motivations/{character_name}/{motivation_id}/complete")
async def complete_motivation(character_name: str, motivation_id: str, note: Optional[str] = None):
    """完成动机"""
    if not motivation_system:
        raise HTTPException(status_code=500, detail="动机系统未初始化")
    
    success = motivation_system.complete_motivation(
        character_name=character_name,
        motivation_id=motivation_id,
        note=note
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="动机不存在")
    
    motivation = motivation_system.get_motivation(character_name, motivation_id)
    return {
        "status": "success",
        "message": "动机已完成",
        "motivation": motivation.to_dict()
    }

@app.delete("/api/motivations/{character_name}/{motivation_id}")
async def abandon_motivation(character_name: str, motivation_id: str, reason: Optional[str] = None):
    """放弃动机"""
    if not motivation_system:
        raise HTTPException(status_code=500, detail="动机系统未初始化")
    
    success = motivation_system.abandon_motivation(
        character_name=character_name,
        motivation_id=motivation_id,
        reason=reason
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="动机不存在")
    
    return {
        "status": "success",
        "message": "动机已放弃"
    }

@app.post("/api/motivations/{character_name}/{motivation_id}/blocker")
async def add_blocker(character_name: str, motivation_id: str, request: MotivationBlockerRequest):
    """添加阻碍因素"""
    if not motivation_system:
        raise HTTPException(status_code=500, detail="动机系统未初始化")
    
    success = motivation_system.add_blocker(
        character_name=character_name,
        motivation_id=motivation_id,
        blocker=request.blocker
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="动机不存在")
    
    return {
        "status": "success",
        "message": "阻碍因素已添加"
    }

@app.get("/api/timeline")
async def get_timeline():
    """获取事件时间线"""
    if not world_engine:
        raise HTTPException(status_code=500, detail="世界引擎未初始化")
    
    return {
        "timeline": world_engine.recent_events,
        "current_time": world_engine.current_time
    }

# ==================== 记忆系统API ====================

@app.post("/api/memory/add")
async def add_memory(request: MemoryAddRequest):
    """添加一条角色记忆"""
    if not memory_system:
        raise HTTPException(status_code=500, detail="记忆系统未初始化")
    
    memory = memory_system.add_memory(
        character_name=request.character_name,
        content=request.content,
        memory_type=request.memory_type,
        metadata=request.metadata
    )
    
    return {
        "status": "success",
        "memory": {
            "character_name": memory.character_name,
            "content": memory.content,
            "memory_type": memory.memory_type,
            "timestamp": memory.timestamp,
            "metadata": memory.metadata
        }
    }

@app.get("/api/memory/{character_name}")
async def get_character_memories(character_name: str):
    """获取角色的所有记忆"""
    if not memory_system:
        raise HTTPException(status_code=500, detail="记忆系统未初始化")
    
    memories = memory_system.get_all_memories(character_name)
    
    return {
        "character_name": character_name,
        "count": len(memories),
        "memories": [
            {
                "content": m.content,
                "memory_type": m.memory_type,
                "timestamp": m.timestamp,
                "metadata": m.metadata
            }
            for m in memories
        ]
    }

@app.get("/api/memory/{character_name}/recent")
async def get_recent_memories(character_name: str, count: int = 10, memory_types: Optional[str] = None):
    """获取角色的最近记忆"""
    if not memory_system:
        raise HTTPException(status_code=500, detail="记忆系统未初始化")
    
    # 解析memory_types字符串为列表
    types = None
    if memory_types:
        types = memory_types.split(',')
    
    memories = memory_system.get_recent_memories(
        character_name=character_name,
        count=count,
        memory_types=types
    )
    
    return {
        "character_name": character_name,
        "count": len(memories),
        "memories": [
            {
                "content": m.content,
                "memory_type": m.memory_type,
                "timestamp": m.timestamp,
                "metadata": m.metadata
            }
            for m in memories
        ]
    }

@app.post("/api/memory/{character_name}/search")
async def search_memories(character_name: str, request: MemorySearchRequest):
    """检索角色的相关记忆"""
    if not memory_system:
        raise HTTPException(status_code=500, detail="记忆系统未初始化")
    
    memories = memory_system.retrieve_memories(
        character_name=character_name,
        query=request.query,
        top_k=request.top_k,
        memory_types=request.memory_types,
        min_similarity=request.min_similarity
    )
    
    return {
        "character_name": character_name,
        "query": request.query,
        "count": len(memories),
        "memories": [
            {
                "content": m.content,
                "memory_type": m.memory_type,
                "timestamp": m.timestamp,
                "metadata": m.metadata
            }
            for m in memories
        ]
    }

@app.delete("/api/memory/{character_name}")
async def clear_character_memories(character_name: str):
    """清除角色的所有记忆"""
    if not memory_system:
        raise HTTPException(status_code=500, detail="记忆系统未初始化")
    
    memory_system.clear_memories(character_name)
    
    return {
        "status": "success",
        "message": f"已清除角色 {character_name} 的记忆"
    }

@app.post("/api/memory/persist")
async def persist_memories():
    """保存所有记忆到磁盘"""
    if not memory_system:
        raise HTTPException(status_code=500, detail="记忆系统未初始化")
    
    memory_system.save_to_disk()
    
    return {
        "status": "success",
        "message": "记忆已保存到磁盘"
    }

@app.post("/api/npc/add")
async def add_npc_to_world(npc_data: Dict):
    """将生成的NPC添加到世界中"""
    if not agent_system:
        raise HTTPException(status_code=500, detail="智能体系统未初始化")
    
    try:
        # 创建一个CharacterAgent作为NPC
        npc_name = npc_data.get("name")
        npc_location = npc_data.get("location", "乡村")
        npc_description = npc_data.get("description", "")
        npc_personality = npc_data.get("personality", [])
        npc_background = npc_data.get("background", "")
        npc_goals = npc_data.get("goals", [])
        npc_role = npc_data.get("role", "路人")
        
        # 创建角色属性
        from tkg_models import CharacterAttributes, CombatPower
        attributes = CharacterAttributes(
            description=npc_description,
            combat_power=CombatPower.UNKNOWN,
            traits=npc_personality,
            background=npc_background
        )
        
        # 获取全局客户端（如果配置了API key）
        npc_client = get_openai_client()
        
        # 创建智能体
        npc_agent = CharacterAgent(
            name=npc_name,
            attributes=attributes,
            relations=[],
            client=npc_client,  # NPC也可以使用LLM进行对话
            memory_system=None if npc_client is None else memory_system,  # 只有在有LLM时才使用记忆系统
            emotion_system=emotion_system,
            motivation_system=motivation_system
        )
        
        # 设置NPC的动态属性
        npc_agent.location = npc_location
        npc_agent.goals = npc_goals
        
        # 添加到智能体系统
        agent_system.agents[npc_name] = npc_agent
        
        # 初始化NPC的情感
        if emotion_system:
            # 为NPC设置初始情感（平静）
            emotion_system.set_emotion(
                npc_name,
                EmotionType.HAPPY,
                intensity=0.3,
                cause="初次登场"
            )
        
        # 初始化NPC的动机
        if motivation_system and npc_goals:
            # 为NPC添加动机
            for goal in npc_goals:
                motivation_system.add_motivation(
                    npc_name,
                    Motivation(
                        description=goal,
                        level=MotivationLevel.MEDIUM_TERM,
                        priority=MotivationPriority.NORMAL,
                        status=MotivationStatus.IN_PROGRESS,
                        progress=0.1
                    )
                )
        
        print(f"✅ NPC '{npc_name}' ({npc_role}) 已添加到世界中")
        
        # 自动保存
        await auto_save_current_world()
        
        return {
            "status": "success",
            "character": npc_name,
            "message": f"NPC '{npc_name}' 已成功添加到世界"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加NPC失败: {str(e)}")

# ==================== 状态持久化API端点 ====================

@app.post("/api/world/state/save")
async def save_world_state():
    """保存当前世界的完整状态"""
    if not world_manager or not current_world_id:
        raise HTTPException(status_code=500, detail="世界管理器未初始化或未加载世界")
    
    try:
        # 收集世界状态
        world_state = {
            "time": world_engine.current_time,
            "locations": world_engine.locations,
            "recent_events": world_engine.recent_events,
            "characters": {}
        }
        
        # 收集所有角色数据
        if agent_system:
            from tkg_models import CharacterAttributes
            for name, agent in agent_system.agents.items():
                chars = world_state["characters"]
                chars[name] = {
                    "attributes": agent.attributes.model_dump() if agent.attributes else {},
                    "location": agent.location,
                    "status": agent.status,
                    "goals": agent.goals,
                    "inventory": agent.inventory,
                    "relations": agent.relations
                }
        
        # 保存到文件
        if world_manager.save_world_state(current_world_id, world_state):
            print(f"✅ 世界状态已保存: {current_world_id}")
            
            # 保存情感状态
            if emotion_system:
                emotions_data = emotion_system.get_all_emotions()
                world_manager.save_emotions(current_world_id, emotions_data)
                print(f"✅ 情感状态已保存: {current_world_id}")
            
            # 保存动机状态
            if motivation_system:
                motivations_data = motivation_system.get_all_motivations()
                world_manager.save_motivations(current_world_id, motivations_data)
                print(f"✅ 动机状态已保存: {current_world_id}")
            
            return {
                "status": "success",
                "message": "世界状态已保存"
            }
        else:
            raise HTTPException(status_code=500, detail="保存失败")
    except Exception as e:
        import traceback
        error_detail = f"保存世界状态失败: {str(e)}\n{traceback.format_exc()}"
        print(f"❌ {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)

@app.post("/api/world/state/load")
async def load_world_state():
    """加载世界状态"""
    if not world_manager or not current_world_id:
        raise HTTPException(status_code=500, detail="世界管理器未初始化或未加载世界")
    
    try:
        state = world_manager.load_world_state(current_world_id)
        if not state:
            raise HTTPException(status_code=404, detail="世界状态文件不存在")
        
        print(f"✅ 正在加载世界状态: {current_world_id}")
        
        # 恢复时间
        if "time" in state:
            world_engine.current_time = state["time"]
        
        # 恢复地点
        if "locations" in state:
            world_engine.locations = state["locations"]
            print(f"   恢复了 {len(world_engine.locations)} 个地点")
        
        # 恢复事件
        if "recent_events" in state:
            world_engine.recent_events = state["recent_events"]
            print(f"   恢复了 {len(world_engine.recent_events)} 个事件")
        
        # 恢复角色
        if "characters" in state and agent_system:
            # 重置agents（不清除已存在的NPC）
            base_chars = set(state["characters"].keys())
            for char_name in list(agent_system.agents.keys()):
                if char_name not in base_chars:
                    # 保留不在保存文件中的NPC
                    continue
            
            # 为保存文件中的角色创建或更新agent
            from tkg_models import CharacterAttributes, CombatPower
            for char_name, char_data in state["characters"].items():
                attrs_data = char_data.get("attributes", {})
                
                # 处理combat_power
                if "combat_power" in attrs_data and attrs_data["combat_power"]:
                    try:
                        attrs_data["combat_power"] = CombatPower(attrs_data["combat_power"])
                    except:
                        attrs_data["combat_power"] = CombatPower.UNKNOWN
                
                attributes = CharacterAttributes(**attrs_data)
                
                if char_name in agent_system.agents:
                    # 更新现有agent
                    agent = agent_system.agents[char_name]
                    agent.attributes = attributes
                    agent.location = char_data.get("location", "未知")
                    agent.status = char_data.get("status", "正常")
                    agent.goals = char_data.get("goals", [])
                    agent.inventory = char_data.get("inventory", [])
                    agent.relations = char_data.get("relations", [])
                else:
                    # 创建新agent（用于重新加载基础角色）
                    from agent_system import CharacterAgent
                    npc_agent = CharacterAgent(
                        name=char_name,
                        attributes=attributes,
                        relations=char_data.get("relations", []),
                        client=get_openai_client(),
                        memory_system=None,
                        emotion_system=emotion_system,
                        motivation_system=motivation_system
                    )
                    npc_agent.location = char_data.get("location", "未知")
                    npc_agent.status = char_data.get("status", "正常")
                    npc_agent.goals = char_data.get("goals", [])
                    npc_agent.inventory = char_data.get("inventory", [])
                    
                    agent_system.agents[char_name] = npc_agent
            
            print(f"   恢复了 {len(state['characters'])} 个角色")
        
        # 恢复情感状态
        if "emotions" in state and emotion_system:
            for char_name, emotion_data in state["emotions"].items():
                if "primary_emotion" in emotion_data:
                    from emotion_system import EmotionType
                    emotion_system.initialize_character(char_name)
                    state_obj = emotion_system.emotion_states[char_name]
                    try:
                        state_obj.primary_emotion = EmotionType(emotion_data["primary_emotion"])
                        state_obj.intensity = emotion_data.get("intensity", 0.0)
                        state_obj.last_updated = emotion_data.get("last_updated", datetime.now().isoformat())
                        if "history" in emotion_data:
                            # 重建历史记录
                            for hist in emotion_data["history"]:
                                try:
                                    state_obj.history.append({
                                        "emotion": EmotionType(hist["emotion"]),
                                        "intensity": hist["intensity"],
                                        "timestamp": hist["timestamp"],
                                        "cause": hist.get("cause", "")
                                    })
                                except:
                                    pass
                    except:
                        pass
            print(f"   恢复了 {len(state['emotions'])} 个角色的情感")
        
        # 恢复动机状态
        if "motivations" in state and motivation_system:
            for char_name, motivations_data in state["motivations"].items():
                for mot_id, mot_data in motivations_data.items():
                    try:
                        from motivation_system import Motivation, MotivationLevel, MotivationPriority, MotivationStatus
                        motivation = Motivation(
                            description=mot_data["description"],
                            level=MotivationLevel(mot_data["level"]),
                            priority=MotivationPriority(mot_data["priority"]),
                            status=MotivationStatus(mot_data["status"]),
                            progress=mot_data.get("progress", 0.0)
                        )
                        motivation.motivation_id = mot_id
                        motivation.created_at = mot_data.get("created_at")
                        motivation.blockers = mot_data.get("blockers", [])
                        motivation.notes = mot_data.get("notes", "")
                        motivation_system.save_motivation(char_name, mot_id, motivation)
                    except:
                        pass
            print(f"   恢复了 {len(state['motivations'])} 个角色的动机")
        
        print(f"✅ 世界状态加载完成: {current_world_id}")
        
        return {
            "status": "success",
            "message": "世界状态已加载"
        }
    except Exception as e:
        import traceback
        error_detail = f"加载世界状态失败: {str(e)}\n{traceback.format_exc()}"
        print(f"❌ {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)

# ==================== 世界管理API端点 ====================

@app.post("/api/worlds")
async def create_world(request: CreateWorldRequest):
    """创建新世界"""
    if not world_manager:
        raise HTTPException(status_code=500, detail="世界管理器未初始化")
    
    try:
        world = world_manager.create_world(
            name=request.name,
            description=request.description,
            template=request.template
        )
        return {
            "status": "success",
            "world": world.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建世界失败: {str(e)}")

@app.get("/api/worlds")
async def list_worlds():
    """列出所有世界"""
    if not world_manager:
        raise HTTPException(status_code=500, detail="世界管理器未初始化")
    
    try:
        worlds = world_manager.list_worlds()
        return {
            "status": "success",
            "worlds": [world.to_dict() for world in worlds]
        }
    except Exception as e:
        import traceback
        error_detail = f"获取世界列表失败: {str(e)}\n{traceback.format_exc()}"
        print(f"❌ {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)

@app.get("/api/worlds/debug")
async def debug_worlds():
    """调试世界管理器状态"""
    if not world_manager:
        return {
            "world_manager": None,
            "error": "世界管理器未初始化"
        }
    
    return {
        "world_manager": "initialized",
        "storage_dir": str(world_manager.storage_dir),
        "worlds_file": str(world_manager.worlds_file),
        "worlds_file_exists": world_manager.worlds_file.exists(),
        "world_data_dir": str(world_manager.worlds_dir),
        "world_data_dir_exists": world_manager.worlds_dir.exists(),
        "worlds_count": len(world_manager.list_worlds()),
        "worlds_list": [w.world_id for w in world_manager.list_worlds()]
    }

@app.get("/api/worlds/{world_id}")
async def get_world(world_id: str):
    """获取指定世界的信息"""
    if not world_manager:
        raise HTTPException(status_code=500, detail="世界管理器未初始化")
    
    world = world_manager.get_world(world_id)
    if not world:
        raise HTTPException(status_code=404, detail="世界不存在")
    
    return {
        "status": "success",
        "world": world.to_dict()
    }

@app.put("/api/worlds/{world_id}")
async def update_world(world_id: str, request: UpdateWorldRequest):
    """更新世界信息"""
    if not world_manager:
        raise HTTPException(status_code=500, detail="世界管理器未初始化")
    
    world = world_manager.update_world(
        world_id=world_id,
        name=request.name,
        description=request.description,
        metadata=request.metadata
    )
    
    if not world:
        raise HTTPException(status_code=404, detail="世界不存在")
    
    return {
        "status": "success",
        "world": world.to_dict()
    }

@app.delete("/api/worlds/{world_id}")
async def delete_world(world_id: str):
    """删除世界"""
    if not world_manager:
        raise HTTPException(status_code=500, detail="世界管理器未初始化")
    
    if world_manager.delete_world(world_id):
        return {
            "status": "success",
            "message": f"世界 {world_id} 已删除"
        }
    else:
        raise HTTPException(status_code=404, detail="世界不存在")

@app.post("/api/worlds/{world_id}/load")
async def load_world(world_id: str):
    """加载指定世界"""
    if not world_manager:
        raise HTTPException(status_code=500, detail="世界管理器未初始化")
    
    world = world_manager.get_world(world_id)
    if not world:
        raise HTTPException(status_code=404, detail="世界不存在")
    
    global current_world_id
    current_world_id = world_id
    
    try:
        # 获取世界数据路径
        world_data_path = world_manager.get_world_data_path(world_id)
        if not world_data_path:
            raise HTTPException(status_code=500, detail="世界数据目录不存在")
        
        # 临时修改data_loader的基础目录以加载指定世界的数据
        # 创建临时的data_loader来加载世界数据
        temp_data_loader = DataLoader()
        temp_data_loader.base_dir = str(world_data_path)
        
        # 加载基础世界数据，传入 world_id 作为 worldline_id
        world_data = temp_data_loader.load_world_data(worldline_id=world_id)
        
        # 初始化智能体系统
        if agent_system:
            agent_system.initialize_agents(world_data)
        
        # 初始化世界引擎
        if world_engine:
            world_engine.initialize(world_data)
        
        # 尝试加载保存的完整状态
        try:
            saved_state = world_manager.load_world_state(world_id)
            if saved_state:
                print(f"📚 发现保存的世界状态，正在恢复...")
                
                # 恢复时间
                if "time" in saved_state:
                    world_engine.current_time = saved_state["time"]
                
                # 恢复地点（包括自动生成的新地点）
                if "locations" in saved_state:
                    world_engine.locations = saved_state["locations"]
                    print(f"   恢复了 {len(world_engine.locations)} 个地点")
                
                # 恢复事件
                if "recent_events" in saved_state:
                    world_engine.recent_events = saved_state["recent_events"]
                
                # 恢复角色数据
                if "characters" in saved_state and agent_system:
                    from tkg_models import CharacterAttributes, CombatPower
                    for char_name, char_data in saved_state["characters"].items():
                        # 跳过无效的字符名（如从旧数据中错误的"characters"键）
                        if char_name in ["characters", "characters_data", "characters_dict"]:
                            continue
                        # 跳过数据结构不正确的项
                        if not isinstance(char_data, dict) or "attributes" not in char_data:
                            continue
                        
                        if char_name not in agent_system.agents:
                            # 创建新的agent（动态添加的NPC）
                            attrs_data = char_data.get("attributes", {})
                            if "combat_power" in attrs_data and attrs_data["combat_power"]:
                                try:
                                    attrs_data["combat_power"] = CombatPower(attrs_data["combat_power"])
                                except:
                                    attrs_data["combat_power"] = CombatPower.UNKNOWN
                            
                            attributes = CharacterAttributes(**attrs_data)
                            npc_agent = CharacterAgent(
                                name=char_name,
                                attributes=attributes,
                                relations=char_data.get("relations", []),
                                client=get_openai_client(),
                                memory_system=None,
                                emotion_system=emotion_system,
                                motivation_system=motivation_system
                            )
                            npc_agent.location = char_data.get("location", "未知")
                            npc_agent.status = char_data.get("status", "正常")
                            npc_agent.goals = char_data.get("goals", [])
                            npc_agent.inventory = char_data.get("inventory", [])
                            agent_system.agents[char_name] = npc_agent
                            
                            print(f"   恢复角色: {char_name}")
                
                # 恢复情感状态
                if "emotions" in saved_state and emotion_system:
                    emotions_dict = saved_state["emotions"]
                    # 处理 EmotionSystem.to_dict() 的格式: {"emotion_states": {char: {...}}}
                    emotion_states = emotions_dict.get("emotion_states", {})
                    for char_name, emotion_data in emotion_states.items():
                        try:
                            from emotion_system import EmotionType, EmotionState
                            emotion_state = EmotionState.from_dict(emotion_data)
                            emotion_system.emotion_states[char_name] = emotion_state
                            print(f"   恢复了 {char_name} 的情感状态")
                        except Exception as e:
                            print(f"   恢复 {char_name} 情感失败: {e}")
                
                # 恢复动机状态
                if "motivations" in saved_state and motivation_system:
                    motivations_dict = saved_state["motivations"]
                    # 处理 MotivationSystem.to_dict() 的格式: {"motivations": {char: [{...}, {...}]}, "relationships": {...}}
                    char_motivations = motivations_dict.get("motivations", {})
                    for char_name, motivations_list in char_motivations.items():
                        try:
                            from motivation_system import Motivation
                            for motivation_data in motivations_list:
                                motivation = Motivation.from_dict(motivation_data)
                                motivation_system.initialize_character(char_name)
                                motivation_system.motivations[char_name].append(motivation)
                            print(f"   恢复了 {char_name} 的 {len(motivations_list)} 个动机")
                        except Exception as e:
                            print(f"   恢复 {char_name} 动机失败: {e}")
                
                print(f"✅ 世界状态已完全恢复")
        except Exception as e:
            print(f"⚠️ 恢复世界状态失败（可能是第一次加载）: {e}")
        
        print(f"✅ 已加载世界: {world.name} (ID: {world_id})")
        
        return {
            "status": "success",
            "world": world.to_dict(),
            "world_data": world_data,
            "characters": list(agent_system.agents.keys()) if agent_system else []
        }
    except Exception as e:
        print(f"❌ 加载世界失败: {e}")
        raise HTTPException(status_code=500, detail=f"加载世界失败: {str(e)}")

@app.get("/api/worlds/{world_id}/export")
async def export_world(world_id: str):
    """导出世界"""
    if not world_manager:
        raise HTTPException(status_code=500, detail="世界管理器未初始化")
    
    world = world_manager.get_world(world_id)
    if not world:
        raise HTTPException(status_code=404, detail="世界不存在")
    
    # 生成导出文件路径
    export_filename = f"{world.name}_{world_id}.zip"
    full_path = os.path.join(world_manager.storage_dir, export_filename)
    
    if world_manager.export_world(world_id, full_path):
        return {
            "status": "success",
            "message": f"世界已导出到 {export_filename}",
            "download_url": f"/api/worlds/{world_id}/download/{export_filename}"
        }
    else:
        raise HTTPException(status_code=500, detail="导出世界失败")

@app.post("/api/worlds/import")
async def import_world(name: str, description: str = "", file=None):
    """导入世界（简化版，文件路径通过其他方式传递）"""
    if not world_manager:
        raise HTTPException(status_code=500, detail="世界管理器未初始化")
    
    # 注意：实际的文件上传需要使用FastAPI的UploadFile
    # 这里提供一个简化版本，假设文件已经上传到服务器
    error_msg = "请使用文件上传接口导入世界"
    raise HTTPException(status_code=501, detail=error_msg)

@app.post("/api/worlds/data/{world_id}/metadata/{metadata_type}")
async def update_world_metadata(world_id: str, metadata_type: str, data: Dict):
    """更新世界的元数据（角色、关系、世界状态等）"""
    if not world_manager:
        raise HTTPException(status_code=500, detail="世界管理器未初始化")
    
    if world_manager.update_world_metadata(world_id, metadata_type, data):
        return {
            "status": "success",
            "message": f"已更新 {metadata_type} 数据"
        }
    else:
        raise HTTPException(status_code=404, detail="世界不存在或更新失败")

@app.post("/api/novel/import")
async def import_novel_text(request: NovelImportRequest):
    """导入小说文本到知识库"""
    if not knowledge_base:
        raise HTTPException(status_code=500, detail="知识库系统未初始化")
    
    try:
        success = knowledge_base.from_novel_text(request.text, request.novel_name)
        if not success:
            raise HTTPException(status_code=400, detail="小说文本导入失败")
        
        # 获取统计信息
        stats = knowledge_base.get_statistics()
        
        return {
            "status": "success",
            "message": f"小说 '{request.novel_name}' 导入成功",
            "statistics": stats
        }
    except Exception as e:
        import traceback
        error_detail = f"导入小说失败: {str(e)}\n{traceback.format_exc()}"
        print(f"❌ {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)

@app.post("/api/novel/query")
async def query_novel_knowledge(request: KnowledgeQueryRequest):
    """查询小说知识库"""
    if not knowledge_base:
        raise HTTPException(status_code=500, detail="知识库系统未初始化")
    
    try:
        result = knowledge_base.retrieve_relevant_content(
            query=request.query,
            top_k=request.top_k
        )
        return {
            "status": "success",
            "query": request.query,
            "result": result
        }
    except Exception as e:
        import traceback
        error_detail = f"查询知识库失败: {str(e)}\n{traceback.format_exc()}"
        print(f"❌ {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)

@app.get("/api/novel/statistics")
async def get_novel_statistics():
    """获取知识库统计信息"""
    if not knowledge_base:
        raise HTTPException(status_code=500, detail="知识库系统未初始化")
    
    try:
        stats = knowledge_base.get_statistics()
        return {
            "status": "success",
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@app.post("/api/novel/create-world")
async def create_world_from_novel(novel_name: str, world_name: Optional[str] = None):
    """从小说知识库创建世界"""
    if not knowledge_base:
        raise HTTPException(status_code=500, detail="知识库系统未初始化")
    if not world_manager:
        raise HTTPException(status_code=500, detail="世界管理器未初始化")
    
    try:
        # 使用 novel_name 作为默认 world_name
        if not world_name:
            world_name = novel_name
        
        # 创建世界
        world = world_manager.create_world(world_name, f"基于小说 '{novel_name}' 创建")
        
        # 从知识库提取数据
        kb_data = knowledge_base.to_dict()
        
        # 创建章节数据目录
        world_dir = world_manager.get_world_data_path(world.world_id)
        import os
        os.makedirs(f"{world_dir}/graphs", exist_ok=True)
        os.makedirs(f"{world_dir}/world_graph", exist_ok=True)
        
        # 生成角色数据
        characters = []
        for char_name, char_info in kb_data.get("characters", {}).items():
            characters.append(char_name)
        
        # 保存角色文件
        char_file = f"{world_dir}/graphs/chapter_001.characters.json"
        with open(char_file, 'w', encoding='utf-8') as f:
            char_data = {
                "characters": {
                    name: {
                        "description": info.get("description", ""),
                        "combat_power": "未知",
                        "traits": info.get("traits", []),
                        "background": info.get("first_appearance", ""),
                        "inventory": []
                    }
                    for name, info in kb_data.get("characters", {}).items()
                }
            }
            json.dump(char_data, f, ensure_ascii=False, indent=2)
        
        # 保存关系文件（简化版本）
        rel_file = f"{world_dir}/graphs/chapter_001.relations.json"
        with open(rel_file, 'w', encoding='utf-8') as f:
            rel_data = {
                "nodes": characters,
                "edges": []  # 可以从文本提取关系，这里留空
            }
            json.dump(rel_data, f, ensure_ascii=False, indent=2)
        
        # 保存世界状态（包含从知识库提取的地点信息）
        state_file = f"{world_dir}/world_graph/chapter_001.json"
        
        # 从事件中构建地点列表
        locations_state = {}
        for loc_name, loc_info in kb_data.get("locations", {}).items():
            locations_state[loc_name] = {
                "name": loc_name,
                "description": loc_info.get("description", ""),
                "type": loc_info.get("type", "未知")
            }
        
        # 为每个角色生成初始目标（AI可以生成，这里用默认）
        goals_state = {}
        for char_name in characters:
            goals_state[char_name] = [
                f"探索{loc_name}" for loc_name in list(kb_data.get("locations", {}).keys())[:2]
            ]
        
        state_data = {
            "worldline_id": world.world_id,
            "chapter_id": 1,
            "title": "第一章",
            "goals": goals_state,
            "locations": locations_state,
            "events": kb_data.get("events", []),
            "initial_time": 0
        }
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 已从小说 '{novel_name}' 创建世界 '{world_name}'")
        
        return {
            "status": "success",
            "message": f"已从小说 '{novel_name}' 创建世界 '{world_name}'",
            "world": world.to_dict(),
            "statistics": {
                "characters_count": len(characters),
                "locations_count": len(kb_data.get("locations", {}))
            }
        }
    except Exception as e:
        import traceback
        error_detail = f"从小说创建世界失败: {str(e)}\n{traceback.format_exc()}"
        print(f"❌ {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

