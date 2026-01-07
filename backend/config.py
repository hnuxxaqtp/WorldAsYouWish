#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理 - 统一管理API配置
"""

import os

# API配置
# 按官方文档要求，使用 https://api.siliconflow.cn/v1 作为基地址
# 参考: https://docs.siliconflow.cn/cn/api-reference/chat-completions/chat-completions
SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
SILICONFLOW_MODEL = "Qwen/Qwen2.5-7B-Instruct"

# API密钥（直接写死，避免每次设置环境变量）
DEFAULT_API_KEY = "sk-rtuewwxhutakmceskujdiluyjakkxdmikddbvjzrubhsbvbv"

# 获取API密钥（优先使用环境变量，否则使用默认值）
def get_api_key():
    """获取API密钥"""
    return os.getenv('SILICONFLOW_API_KEY') or os.getenv('OPENAI_API_KEY') or DEFAULT_API_KEY

# 检查API密钥是否配置
def is_api_configured():
    """检查API密钥是否已配置"""
    return get_api_key() is not None

