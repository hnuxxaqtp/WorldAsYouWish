#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NPC自动生成系统 - 根据世界状态自动生成路人NPC
"""

from typing import Dict, List, Optional, Any
from enum import Enum
import random
import json
from datetime import datetime


class NPCRole(Enum):
    """NPC角色类型"""
    VILLAGER = "村民"
    MERCHANT = "商人"
    GUARD = "守卫"
    TRAVELER = "旅行者"
    ARTISAN = "工匠"
    FARMER = "农民"
    SCHOLAR = "学者"
    HEALER = "治疗师"
    BARD = "吟游诗人"
    THIEF = "盗贼"
    NOBLE = "贵族"
    SERVANT = "仆人"
    CHILD = "孩子"
    ELDER = "老人"
    ADVENTURER = "冒险者"


class NPCAppearance(Enum):
    """外貌特征"""
    HAIR_COLOR = ["黑色", "棕色", "金色", "银色", "红色", "灰色", "白色"]
    EYE_COLOR = ["黑色", "棕色", "蓝色", "绿色", "琥珀色", "灰色"]
    HEIGHT = ["矮小", "中等", "高大"]
    BUILD = ["瘦弱", "匀称", "壮实", "肥胖"]
    SKIN_TONE = ["白皙", "中等", "小麦色", "深色"]


class NPCPersonality(Enum):
    """性格特征"""
    CHEERFUL = "开朗"
    SHY = "害羞"
    BRAVE = "勇敢"
    COWARDLY = "胆小"
    WISE = "智慧"
    NAIVE = "天真"
    KIND = "善良"
    CRUEL = "残酷"
    LAZY = "懒惰"
    DILIGENT = "勤奋"
    ARROGANT = "傲慢"
    HUMBLE = "谦逊"
    CURIOUS = "好奇"
    CAUTIOUS = "谨慎"


class NPC:
    """NPC类"""
    
    def __init__(
        self,
        name: str,
        role: NPCRole,
        description: str,
        location: str,
        personality: List[str],
        appearance: Dict[str, str],
        background: str,
        goals: List[str],
        relationships: Optional[Dict] = None
    ):
        self.name = name
        self.role = role
        self.description = description
        self.location = location
        self.personality = personality
        self.appearance = appearance
        self.background = background
        self.goals = goals
        self.relationships = relationships or {}
        self.created_at = datetime.now().isoformat()
        self.is_npc = True  # 标记为NPC
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "name": self.name,
            "role": self.role.value,
            "description": self.description,
            "location": self.location,
            "personality": self.personality,
            "appearance": self.appearance,
            "background": self.background,
            "goals": self.goals,
            "relationships": self.relationships,
            "created_at": self.created_at,
            "is_npc": True
        }


class NPCGenerator:
    """NPC生成器"""
    
    def __init__(self):
        self.name_templates = self._load_name_templates()
        self.role_templates = self._load_role_templates()
    
    def _load_name_templates(self) -> Dict[str, List[str]]:
        """加载姓名模板"""
        return {
            "male_surnames": [
                "张", "李", "王", "赵", "刘", "陈", "杨", "黄", "周", "吴",
                "徐", "孙", "胡", "朱", "高", "林", "何", "郭", "马", "罗"
            ],
            "male_given_names": [
                "伟", "强", "磊", "洋", "勇", "军", "杰", "涛", "超", "明",
                "刚", "平", "辉", "鹏", "华", "飞", "鑫", "波", "斌", "宇"
            ],
            "female_surnames": [
                "陈", "林", "张", "李", "王", "刘", "吴", "杨", "黄", "周"
            ],
            "female_given_names": [
                "芳", "娜", "敏", "静", "丽", "娟", "燕", "秀英", "桂英", "玉兰",
                "小红", "小芳", "小丽", "晓慧", "雅琴", "美玲", "淑华", "素芬", "雪梅"
            ]
        }
    
    def _load_role_templates(self) -> Dict[NPCRole, Dict]:
        """加载角色模板"""
        return {
            NPCRole.VILLAGER: {
                "description_templates": [
                    "一个居住在{location}的普通村民",
                    "在{location}生活的{personality}村民",
                    "{location}的本地居民"
                ],
                "background_templates": [
                    "在{location}出生长大，熟悉这里的一草一木",
                    "世代居住在{location}的居民",
                    "从外地搬到{location}，已经生活了数年"
                ],
                "goal_templates": [
                    "希望能过上安稳的生活",
                    "期待村里有个好年景",
                    "想和邻里和睦相处",
                    "希望能攒够钱改善生活"
                ]
            },
            NPCRole.MERCHANT: {
                "description_templates": [
                    "一位{personality}的商人",
                    "来往于各地的商人",
                    "在{location}做买卖的商人"
                ],
                "background_templates": [
                    "经商多年，走南闯北，见多识广",
                    "继承了家族的商号，继续经营生意",
                    "白手起家做起了生意"
                ],
                "goal_templates": [
                    "扩大生意规模",
                    "找到更多贸易伙伴",
                    "赚更多的钱",
                    "建立自己的商队"
                ]
            },
            NPCRole.GUARD: {
                "description_templates": [
                    "一名{personality}的守卫",
                    "负责维护{location}治安的守卫",
                    "一位尽职尽责的守卫"
                ],
                "background_templates": [
                    "受过正规训练的卫兵",
                    "退伍后成为守卫",
                    "因为力量出众被选中当守卫"
                ],
                "goal_templates": [
                    "维护地方的和平与安全",
                    "保护居民不受伤害",
                    "希望能升职加薪",
                    "抓捕所有违法犯罪的人"
                ]
            },
            NPCRole.TRAVELER: {
                "description_templates": [
                    "一个{personality}的旅行者",
                    "途经{location}的旅人",
                    "正在四处游历的旅行者"
                ],
                "background_templates": [
                    "离家远行，寻找失散的亲人",
                    "为了寻找某些秘密而四处旅行",
                    "纯粹是为了体验各地的风土人情"
                ],
                "goal_templates": [
                    "完成此次旅行的目的",
                    "找到下一个落脚点",
                    "在路上结识新的朋友",
                    "记录旅途中的所见所闻"
                ]
            },
            NPCRole.ARTISAN: {
                "description_templates": [
                    "一位技艺精湛的工匠",
                    "在{location}受人尊敬的工匠",
                    "一个{personality}的工匠"
                ],
                "background_templates": [
                    "从小就学习手艺，如今已是大师",
                    "因为手艺出色而远近闻名",
                    "为了追求技艺的极致而不断努力"
                ],
                "goal_templates": [
                    "创造一件传世之作",
                    "将手艺传授给后人",
                    "获得贵族的赏识",
                    "开设自己的工坊"
                ]
            },
            NPCRole.FARMER: {
                "description_templates": [
                    "一位朴实的农民",
                    "在{location}种地的农夫",
                    "一个{personality}的农民"
                ],
                "background_templates": [
                    "世代务农，对土地有着深厚的感情",
                    "辛苦劳作养活家人",
                    "今年收成不错，心情很好"
                ],
                "goal_templates": [
                    "今年能有个好收成",
                    "攒钱买更多的土地",
                    "让孩子们过上更好的生活",
                    "学习新的耕种技术"
                ]
            },
            NPCRole.SCHOLAR: {
                "description_templates": [
                    "一位博学的学者",
                    "正在{location}研究的学者",
                    "一个{personality}的学者"
                ],
                "background_templates": [
                    "师从名师，学富五车",
                    "花费数年时间钻研某个领域",
                    "为了一个重要的研究课题来到这里"
                ],
                "goal_templates": [
                    "完成自己的研究",
                    "找到需要的古籍或资料",
                    "传播知识",
                    "解开某个谜团"
                ]
            },
            NPCRole.HEALER: {
                "description_templates": [
                    "一位{personality}的治疗师",
                    "在{location}行医治疗师",
                    "一位技艺高超的医师"
                ],
                "background_templates": [
                    "师承名医，医术精湛",
                    "因为一次特殊的经历而开始行医",
                    "在救助过许多病人"
                ],
                "goal_templates": [
                    "救死扶伤",
                    "研制新的药物",
                    "治愈更多病人",
                    "学习更高级的治疗术"
                ]
            },
            NPCRole.BARD: {
                "description_templates": [
                    "一位{personality}的吟游诗人",
                    "正在{location}表演的诗人",
                    "一位受欢迎的吟游诗人"
                ],
                "background_templates": [
                    "游历各地，收集和创作诗歌",
                    "为了传播英雄事迹而四处演唱",
                    "天赋异禀，歌声优美动人"
                ],
                "goal_templates": [
                    "创作更多动人的诗歌",
                    "传播真实的故事",
                    "成为著名的吟游诗人",
                    "找到传说中的旋律"
                ]
            },
            NPCRole.THIEF: {
                "description_templates": [
                    "一个狡猾的{personality}的小偷",
                    "在{location}活动的盗贼",
                    "一个经验丰富的盗贼"
                ],
                "background_templates": [
                    "因为生活所迫而走上这条路",
                    "为了追求自由自在的生活",
                    "曾经也是普通人，后来学会了偷盗"
                ],
                "goal_templates": [
                    "偷到有价值的财物",
                    "不被抓住",
                    "攒够钱改过自新",
                    "找到传说中的宝藏"
                ]
            },
            NPCRole.NOBLE: {
                "description_templates": [
                    "一位{personality}的贵族",
                    "一位来自远方的贵族",
                    "一位举止优雅的贵族"
                ],
                "background_templates": [
                    "出生于贵族家庭，从小接受良好教育",
                    "因为家族功绩获得爵位",
                    "富有的贵族，在各地都有产业"
                ],
                "goal_templates": [
                    "维护家族的声誉",
                    "扩大领地",
                    "获得更高的爵位",
                    "提升家族的影响力"
                ]
            },
            NPCRole.SERVANT: {
                "description_templates": [
                    "一位{personality}的仆人",
                    "在{location}工作的仆人",
                    "一个勤恳的仆人"
                ],
                "background_templates": [
                    "从小就在豪门当仆",
                    "为了生计而在此工作",
                    "因为主人信任而负责重要事务"
                ],
                "goal_templates": [
                    "完成主人的吩咐",
                    "攒钱买回自由",
                    "获得主人的赏识",
                    "改善自己的处境"
                ]
            },
            NPCRole.CHILD: {
                "description_templates": [
                    "一个{personality}的孩子",
                    "在{location}玩耍的孩子",
                    "一位活泼可爱的孩童"
                ],
                "background_templates": [
                    "在{location}长大的孩子",
                    "跟随父母来到这里",
                    "对世界充满好奇"
                ],
                "goal_templates": [
                    "探索外面的世界",
                    "交到好朋友",
                    "学到新的本领",
                    "找到好玩的玩具"
                ]
            },
            NPCRole.ELDER: {
                "description_templates": [
                    "一位{personality}的老人",
                    "在{location}生活多年的老人",
                    "一位受人尊敬的长者"
                ],
                "background_templates": [
                    "在{location}生活了一辈子",
                    "经历过许多事情，见多识广",
                    "德高望重，受人尊敬"
                ],
                "goal_templates": [
                    "安度晚年",
                    "将自己的经验传授给后人",
                    "看着孩子们健康成长",
                    "解决一些遗留的问题"
                ]
            },
            NPCRole.ADVENTURER: {
                "description_templates": [
                    "一位{personality}的冒险者",
                    "正在{location}探险的冒险者",
                    "一个经验丰富的冒险者"
                ],
                "background_templates": [
                    "为了挑战自我成为冒险者",
                    "受人之托完成冒险任务",
                    "寻找传说中的宝物"
                ],
                "goal_templates": [
                    "完成当前的冒险任务",
                    "发现新的冒险",
                    "变得更强",
                    "建立自己的传奇故事"
                ]
            }
        }
    
    def generate_name(self, gender: str = "random") -> str:
        """生成姓名"""
        if gender == "random":
            gender = random.choice(["male", "female"])
        
        if gender == "male":
            surname = random.choice(self.name_templates["male_surnames"])
            given_name = random.choice(self.name_templates["male_given_names"])
        else:
            surname = random.choice(self.name_templates["female_surnames"])
            given_name = random.choice(self.name_templates["female_given_names"])
        
        return surname + given_name
    
    def generate_appearance(self) -> Dict[str, str]:
        """生成外貌特征"""
        return {
            "hair_color": random.choice(NPCAppearance.HAIR_COLOR.value),
            "eye_color": random.choice(NPCAppearance.EYE_COLOR.value),
            "height": random.choice(NPCAppearance.HEIGHT.value),
            "build": random.choice(NPCAppearance.BUILD.value),
            "skin_tone": random.choice(NPCAppearance.SKIN_TONE.value)
        }
    
    def generate_personality(self, count: int = 2) -> List[str]:
        """生成性格特征"""
        traits = [trait.value for trait in NPCPersonality]
        return random.sample(traits, min(count, len(traits)))
    
    def generate_description(self, role: NPCRole, location: str, personality: List[str]) -> str:
        """生成角色描述"""
        template = random.choice(self.role_templates[role]["description_templates"])
        return template.format(
            location=location,
            personality=personality[0] if personality else ""
        )
    
    def generate_background(self, role: NPCRole, location: str) -> str:
        """生成背景故事"""
        template = random.choice(self.role_templates[role]["background_templates"])
        return template.format(location=location)
    
    def generate_goals(self, role: NPCRole, count: int = 2) -> List[str]:
        """生成目标"""
        templates = self.role_templates[role]["goal_templates"]
        return random.sample(templates, min(count, len(templates)))
    
    def generate_npc(
        self,
        role: Optional[NPCRole] = None,
        location: str = "乡村",
        gender: str = "random"
    ) -> NPC:
        """
        生成一个NPC
        
        Args:
            role: 角色类型（None则随机选择）
            location: 所在地点
            gender: 性别（male/female/random）
        
        Returns:
            NPC对象
        """
        # 随机选择角色类型
        if role is None:
            role = random.choice(list(NPCRole))
        
        # 生成姓名
        name = self.generate_name(gender)
        
        # 生成外貌
        appearance = self.generate_appearance()
        
        # 生成性格
        personality = self.generate_personality()
        
        # 生成描述
        description = self.generate_description(role, location, personality)
        
        # 生成背景
        background = self.generate_background(role, location)
        
        # 生成目标
        goals = self.generate_goals(role)
        
        return NPC(
            name=name,
            role=role,
            description=description,
            location=location,
            personality=personality,
            appearance=appearance,
            background=background,
            goals=goals
        )
    
    def generate_npc_batch(
        self,
        count: int,
        location: str,
        allowed_roles: Optional[List[NPCRole]] = None
    ) -> List[NPC]:
        """
        批量生成NPC
        
        Args:
            count: 生成的NPC数量
            location: 所在地点
            allowed_roles: 允许的角色类型（None则使用全部角色）
        
        Returns:
            NPC列表
        """
        npcs = []
        
        if allowed_roles is None:
            allowed_roles = list(NPCRole)
        
        for _ in range(count):
            role = random.choice(allowed_roles)
            npc = self.generate_npc(role=role, location=location)
            npcs.append(npc)
        
        return npcs