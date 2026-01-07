#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载记忆模型到项目目录
使用方法: python download_model.py
"""

import os
from sentence_transformers import SentenceTransformer

# 配置
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

def main():
    print("=" * 60)
    print("记忆模型下载工具")
    print("=" * 60)
    print()
    
    # 确定模型保存路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_dir = os.path.join(script_dir, "model", MODEL_NAME.replace("/", "--"))
    
    print(f"模型名称: {MODEL_NAME}")
    print(f"保存路径: {model_dir}")
    print()
    
    # 检查模型是否已存在
    if os.path.exists(model_dir):
        print(f"⚠️  模型目录已存在: {model_dir}")
        print(f"文件列表:")
        try:
            files = os.listdir(model_dir)
            for f in files[:10]:
                print(f"  - {f}")
            if len(files) > 10:
                print(f"  ... 还有 {len(files) - 10} 个文件")
            
            choice = input("\n是否重新下载？(y/N): ").strip().lower()
            if choice != 'y':
                print("已取消下载")
                return
        except Exception as e:
            print(f"无法列出文件: {e}")
    
    # 确保目录存在
    os.makedirs(os.path.dirname(model_dir), exist_ok=True)
    
    # 下载模型
    print("开始下载模型...")
    print("注意：首次下载可能需要几分钟时间")
    print()
    
    try:
        # 加载模型（会自动下载到缓存）
        print("正在从 huggingface.co 下载模型...")
        model = SentenceTransformer(MODEL_NAME)
        
        # 保存到指定目录
        print(f"正在复制模型文件到: {model_dir}")
        model.save(model_dir)
        
        print()
        print("=" * 60)
        print("✅ 模型下载完成！")
        print("=" * 60)
        print()
        print("模型已保存到:")
        print(f"  {model_dir}")
        print()
        print("现在可以离线使用记忆系统了！")
        print()
        
        # 显示文件大小
        total_size = 0
        file_count = 0
        for root, dirs, files in os.walk(model_dir):
            for file in files:
                file_path = os.path.join(root, file)
                total_size += os.path.getsize(file_path)
                file_count += 1
        
        size_mb = total_size / (1024 * 1024)
        print(f"模型文件数: {file_count}")
        print(f"总大小: {size_mb:.2f} MB")
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ 下载失败")
        print("=" * 60)
        print(f"错误信息: {e}")
        print()
        print("请检查:")
        print("1. 网络连接是否正常")
        print("2. 是否能访问 huggingface.co")
        print("3. Python 版本是否支持")
        print()

if __name__ == "__main__":
    main()