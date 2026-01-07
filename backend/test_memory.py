#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆系统测试脚本
"""

from memory_system import MemorySystem
import json

def test_memory_system():
    print("===== 记忆系统测试 =====\n")
    
    # 创建记忆系统
    print("1. 初始化记忆系统...")
    memory_system = MemorySystem()
    print("   ✅ 记忆系统初始化完成\n")
    
    # 添加测试记忆
    print("2. 添加测试记忆...")
    memory_system.add_memory(
        character_name="张三",
        content="我和李四进行了对话，讨论了关于魔法的知识",
        memory_type="dialogue",
        metadata={"listener": "李四", "topic": "魔法知识"}
    )
    
    memory_system.add_memory(
        character_name="张三",
        content="我在图书馆发现了一本古老的魔法书",
        memory_type="action",
        metadata={"location": "图书馆", "item": "魔法书"}
    )
    
    memory_system.add_memory(
        character_name="张三",
        content="李四在训练场练习剑术，看起来很生气",
        memory_type="observation",
        metadata={"location": "训练场", "target": "李四", "emotion": "生气"}
    )
    
    memory_system.add_memory(
        character_name="李四",
        content="张三建议我们要一起探索古老的遗迹",
        memory_type="dialogue",
        metadata={"listener": "张三", "topic": "探索遗迹"}
    )
    
    print(f"   ✅ 已添加记忆\n")
    
    # 测试检索
    print("3. 测试记忆检索...")
    query = "图书馆 魔法书"
    results = memory_system.retrieve_memories(
        character_name="张三",
        query=query,
        top_k=3
    )
    print(f"   查询: {query}")
    print(f"   找到 {len(results)} 条相关记忆:")
    for i, memory in enumerate(results, 1):
        print(f"     {i}. [{memory.memory_type}] {memory.content}\n")
    
    # 获取最近记忆
    print("4. 获取最近记忆...")
    recent = memory_system.get_recent_memories(
        character_name="张三",
        count=2
    )
    print(f"   张三的最近 2 条记忆:")
    for i, memory in enumerate(recent, 1):
        print(f"     {i}. [{memory.memory_type}] {memory.timestamp[:19]} - {memory.content}\n")
    
    # 格式化记忆
    print("5. 格式化记忆用于提示词...")
    formatted = memory_system.format_memories_for_prompt(results)
    print("   格式化结果:")
    print("   " + "\n   ".join(formatted.split('\n')) + "\n")
    
    # 保存到磁盘
    print("6. 保存记忆到磁盘...")
    memory_system.save_to_disk()
    print("   ✅ 记忆已保存\n")
    
    # 测试清除记忆
    print("7. 测试清除记忆...")
    memory_system.clear_memories("张三")
    print("   ✅ 已清除张三的记忆")
    remaining = memory_system.get_all_memories("张三")
    print(f"   张三当前记忆数量: {len(remaining)}\n")
    
    # 从磁盘加载
    print("8. 从磁盘加载记忆...")
    memory_system.load_from_disk()
    loaded = memory_system.get_all_memories("张三")
    print(f"   ✅ 已从磁盘加载记忆")
    print(f"   张三记忆数量: {len(loaded)}")
    
    print("\n===== 测试完成 =====")

if __name__ == "__main__":
    test_memory_system()