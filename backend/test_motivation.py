#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动机系统测试脚本 - 为角色添加示例动机并测试完整功能
"""
import sys
sys.path.insert(0, '.')

from motivation_system import MotivationSystem, Motivation, MotivationLevel, MotivationPriority, MotivationStatus

# 创建动机系统
motivation_system = MotivationSystem()

# 定义示例角色和他们的动机
character_motivations = {
    "银发少女": [
        # 长期目标
        Motivation(
            description="探索这个世界的秘密，寻找回到故乡的方法",
            level=MotivationLevel.LONG_TERM,
            priority=MotivationPriority.HIGH,
            status=MotivationStatus.IN_PROGRESS,
            progress=0.2
        ),
        
        Motivation(
            description="阻止即将到来的灾难，守护这个世界",
            level=MotivationLevel.LONG_TERM,
            priority=MotivationPriority.CRITICAL,
            status=MotivationStatus.IN_PROGRESS,
            progress=0.1
        ),
        
        # 中期目标
        Motivation(
            description="与旅行者建立互信关系",
            level=MotivationLevel.MEDIUM_TERM,
            priority=MotivationPriority.HIGH,
            status=MotivationStatus.IN_PROGRESS,
            progress=0.5,
            sub_goals=["进行深入对话", "分享自己的秘密", "帮助旅行者"]
        ),
        
        Motivation(
            description="收集关于灾难的信息和线索",
            level=MotivationLevel.MEDIUM_TERM,
            priority=MotivationPriority.HIGH,
            status=MotivationStatus.IN_PROGRESS,
            progress=0.3,
            sub_goals=["调查古老遗迹", "询问村长", "询问旅行商人"]
        ),
        
        # 短期目标
        Motivation(
            description="探索附近的村庄，了解当地情况",
            level=MotivationLevel.SHORT_TERM,
            priority=MotivationPriority.NORMAL,
            status=MotivationStatus.COMPLETED,
            progress=1.0
        ),
        
        Motivation(
            description="与村长交流，获取更多信息",
            level=MotivationLevel.SHORT_TERM,
            priority=MotivationPriority.HIGH,
            status=MotivationStatus.IN_PROGRESS,
            progress=0.6
        ),
    ],
    
    "旅行者": [
        # 长期目标
        Motivation(
            description="揭开这个世界的真相",
            level=MotivationLevel.LONG_TERM,
            priority=MotivationPriority.NORMAL,
            status=MotivationStatus.IN_PROGRESS,
            progress=0.15
        ),
        
        # 中期目标
        Motivation(
            description="提升自己的能力，保护同伴",
            level=MotivationLevel.MEDIUM_TERM,
            priority=MotivationPriority.HIGH,
            status=MotivationStatus.IN_PROGRESS,
            progress=0.4,
            sub_goals=["学习新的技能", "收集更好的装备"]
        ),
        
        # 短期目标
        Motivation(
            description="与银发少女建立友好关系",
            level=MotivationLevel.SHORT_TERM,
            priority=MotivationPriority.HIGH,
            status=MotivationStatus.IN_PROGRESS,
            progress=0.7
        ),
        
        Motivation(
            description="调查村子的异常情况",
            level=MotivationLevel.SHORT_TERM,
            priority=MotivationPriority.NORMAL,
            status=MotivationStatus.PENDING,
            progress=0.0
        ),
    ],
    
    "村长": [
        # 长期目标
        Motivation(
            description="守护村子的安宁，保护村民",
            level=MotivationLevel.LONG_TERM,
            priority=MotivationPriority.HIGH,
            status=MotivationStatus.IN_PROGRESS,
            progress=0.6
        ),
        
        # 中期目标
        Motivation(
            description="帮助银发少女和旅行者",
            level=MotivationLevel.MEDIUM_TERM,
            priority=MotivationPriority.NORMAL,
            status=MotivationStatus.IN_PROGRESS,
            progress=0.5
        ),
        
        # 短期目标
        Motivation(
            description="处理村子的日常事务",
            level=MotivationLevel.SHORT_TERM,
            priority=MotivationPriority.NORMAL,
            status=MotivationStatus.IN_PROGRESS,
            progress=0.8
        ),
    ],
    
    "商人": [
        # 长期目标
        Motivation(
            description="扩大生意，建立贸易网络",
            level=MotivationLevel.LONG_TERM,
            priority=MotivationPriority.NORMAL,
            status=MotivationStatus.IN_PROGRESS,
            progress=0.3
        ),
        
        # 中期目标
        Motivation(
            description="收集稀有的商品",
            level=MotivationLevel.MEDIUM_TERM,
            priority=MotivationPriority.NORMAL,
            status=MotivationStatus.IN_PROGRESS,
            progress=0.4
        ),
        
        # 短期目标
        Motivation(
            description="向旅行者推销商品",
            level=MotivationLevel.SHORT_TERM,
            priority=MotivationPriority.HIGH,
            status=MotivationStatus.PENDING,
            progress=0.0
        ),
    ]
}

print("=" * 60)
print("开始添加动机数据...")
print("=" * 60)

total_added = 0
for character_name, motivations in character_motivations.items():
    print(f"\n📝 为角色 [{character_name}] 添加动机...")
    for motivation in motivations:
        result = motivation_system.add_motivation(character_name, motivation)
        if result:
            total_added += 1
            print(f"  ✅ 添加动机: {motivation.description[:30]}... [{motivation.level.value}][{motivation.priority.value}]")
        else:
            print(f"  ❌ 添加失败: {motivation.description[:30]}...")
    
    # 显示摘要
    summary = motivation_system.get_motivation_summary(character_name)
    print(f"\n  📊 [{character_name}] 动机摘要:")
    print(f"     总数: {summary['total']}")
    print(f"     按层级: 短期={summary['by_level']['短期']}, 中期={summary['by_level']['中期']}, 长期={summary['by_level']['长期']}")
    print(f"     完成率: {(summary['completion_rate'] * 100):.1f}%")

print("\n" + "=" * 60)
print(f"✅ 共添加了 {total_added} 个动机！")
print("=" * 60)

# 测试格式化用于规划的文本
print("\n📋 测试规划格式化:")
print("=" * 60)
for character_name in character_motivations.keys():
    planning_text = motivation_system.format_for_planning(character_name)
    print(f"\n【{character_name}】")
    print(planning_text)

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)

# 提示用户
print("\n💡 提示:")
print("  1. 后端API现在应该可以返回动机数据了")
print("  2. 前端角色面板会显示每个角色的动机信息")
print("  3. 如果前端仍看不到，请刷新浏览器页面")
print("  4. 确保后端服务正在运行")