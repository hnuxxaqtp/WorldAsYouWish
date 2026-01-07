from pydantic import BaseModel, Field, ValidationError
from typing import List, Dict, Optional, Literal

RelationType = Literal["盟友","对立","亲密","上下级","债务","同事","陌生","家人","同伴"]
Polarity = Literal[-1, 0, 1]

class Event(BaseModel):
    who: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)
    target: Optional[str] = None
    goal: Optional[str] = None
    polarity: Optional[Polarity] = 0
    time: Optional[str] = None
    location: Optional[str] = None
    precond: Optional[str] = None
    effect: Optional[str] = None

class Relation(BaseModel):
    a: str
    b: str
    type: RelationType
    score: float = Field(ge=0.0, le=1.0)

class NarrativeState(BaseModel):
    chapter_id: int
    title: str
    events: List[Event] = []
    relations: List[Relation] = []
    goals: Dict[str, List[str]] = {}
    objects: Dict[str, str] = {}      # 关键道具: 状态/持有者/位置 等自由文本短语
    meta: Dict[str, str] = {}         # 额外元数据（worldline_id, word_count等）
