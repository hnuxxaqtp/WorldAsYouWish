#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API连接
"""

import os
from config import get_api_key, SILICONFLOW_BASE_URL, is_api_configured
from openai import OpenAI

def test_api_connection():
    """测试API连接"""
    print("=" * 50)
    print("测试 SiliconFlow API 连接")
    print("=" * 50)
    
    # 检查环境变量
    print("\n1. 检查环境变量:")
    print(f"   SILICONFLOW_API_KEY: {'已设置' if os.getenv('SILICONFLOW_API_KEY') else '未设置'}")
    print(f"   OPENAI_API_KEY: {'已设置' if os.getenv('OPENAI_API_KEY') else '未设置'}")
    
    # 检查API key
    api_key = get_api_key()
    if not api_key:
        print("\n❌ 未找到API Key！")
        print("   请设置环境变量:")
        print("   Windows: set SILICONFLOW_API_KEY=your-key")
        print("   Linux/Mac: export SILICONFLOW_API_KEY=your-key")
        return False
    
    print(f"\n2. API Key: {api_key[:10]}...{api_key[-10:]}")
    print(f"   Base URL: {SILICONFLOW_BASE_URL}")
    
    # 测试连接
    print("\n3. 测试API连接...")
    try:
        client = OpenAI(
            api_key=api_key,
            base_url=SILICONFLOW_BASE_URL
        )
        
        # 发送测试请求
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-7B-Instruct",
            messages=[
                {"role": "user", "content": "你好，请回复'测试成功'"}
            ],
            max_tokens=50
        )
        
        result = response.choices[0].message.content
        print(f"✅ API连接成功！")
        print(f"   模型响应: {result}")
        return True
        
    except Exception as e:
        print(f"❌ API连接失败: {e}")
        print(f"   错误类型: {type(e).__name__}")
        return False

if __name__ == "__main__":
    test_api_connection()

