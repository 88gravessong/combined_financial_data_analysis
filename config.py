#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件 - 财务数据分析系统
包含汇率、操作费等可配置参数
"""

import os
from typing import Dict

# ============ 汇率配置 ============
# 印尼盾汇率（可通过环境变量覆盖）
IDR_PER_RMB = float(os.getenv('IDR_PER_RMB', '2300'))   # 印尼盾对人民币
IDR_PER_USD = float(os.getenv('IDR_PER_USD', '16000'))  # 印尼盾对美元

# 马来币汇率（可通过环境变量覆盖）
MYR_PER_RMB = float(os.getenv('MYR_PER_RMB', '0.6'))    # 马来币对人民币

# ============ 操作费配置 ============
# 印尼模块操作费（人民币）
INDONESIA_OPERATION_FEE = {
    'single_item': float(os.getenv('IDN_OP_FEE_SINGLE', '2.0')),    # 单品订单
    'multi_item': float(os.getenv('IDN_OP_FEE_MULTI', '2.5'))       # 多品订单
}

# 马来模块操作费（马来币）
MALAYSIA_OPERATION_FEE: Dict[str, float] = {
    'xifashui': float(os.getenv('MYR_OP_FEE_XIFASHUI', '2.5')),
    'kingstick': float(os.getenv('MYR_OP_FEE_KINGSTICK', '2.5')),
    'default': float(os.getenv('MYR_OP_FEE_DEFAULT', '2.5'))
}

# ============ 文件处理配置 ============
# 支持的文件扩展名
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

# 最大文件大小（字节）
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', str(50 * 1024 * 1024)))  # 50MB

# ============ Web服务配置 ============
# Flask配置
FLASK_CONFIG = {
    'host': os.getenv('FLASK_HOST', '127.0.0.1'),
    'port': int(os.getenv('FLASK_PORT', '8080')),
    'debug': os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
}

# ============ 日志配置 ============
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

def get_exchange_rates():
    """获取当前汇率配置"""
    return {
        'IDR_PER_RMB': IDR_PER_RMB,
        'IDR_PER_USD': IDR_PER_USD, 
        'MYR_PER_RMB': MYR_PER_RMB
    }

def get_operation_fees():
    """获取当前操作费配置"""
    return {
        'indonesia': INDONESIA_OPERATION_FEE,
        'malaysia': MALAYSIA_OPERATION_FEE
    }

def print_config():
    """打印当前配置（用于调试）"""
    print("📋 当前系统配置:")
    print(f"  汇率配置: IDR/RMB={IDR_PER_RMB}, IDR/USD={IDR_PER_USD}, MYR/RMB={MYR_PER_RMB}")
    print(f"  文件大小限制: {MAX_FILE_SIZE // (1024*1024)}MB")
    print(f"  Flask配置: {FLASK_CONFIG}")
    print(f"  日志级别: {LOG_LEVEL}")

if __name__ == "__main__":
    print_config()