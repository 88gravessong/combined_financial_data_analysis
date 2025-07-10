#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analysis_mal.py
------------------------------------------------
马来跨境店财务数据分析模块
- 支持多个订单表文件合并
- 支持多个结算表文件合并
- 单个产品消耗表
"""

import pandas as pd
import numpy as np
from openpyxl import load_workbook
from pathlib import Path
from typing import List, Union
from config import get_exchange_rates, get_operation_fees

# === 配置参数 ===
# 注意：这些路径仅用于说明文件格式，实际使用时通过函数参数传入
# orders_path     = '马7-1.1至4.30订单.xlsx'          # 订单表（第 2 行为注释）
# settlement_path = '马七 下 income_20250530073840.xlsx'  # 结算表
# cost_path       = '产品成本消耗表.xlsx'              # 产品成本消耗表
# output_path     = '订单_汇总_成本利润.xlsx'

# 动态获取汇率和操作费配置
exchange_rates = get_exchange_rates()
MYR_PER_RMB = exchange_rates['MYR_PER_RMB']

# 出库订单操作费（RM）- 从配置文件获取
OP_FEE = get_operation_fees()['malaysia']

def merge_order_files_mal(order_files: List[Union[str, Path]]) -> pd.DataFrame:
    """合并多个马来订单表文件（跳过第2行注释）"""
    all_orders = []
    
    for file_path in order_files:
        try:
            # 使用openpyxl读取，跳过第2行注释
            wb = load_workbook(file_path, data_only=True)
            rows = [[c for c in row] for row in wb.active.values]
            header = [str(c).strip() if c else "" for c in rows[0]]
            
            # 跳过第2行注释，从第3行开始读取数据
            df = pd.DataFrame(rows[2:], columns=header).dropna(subset=['Order ID'])
            df.columns = df.columns.str.strip()
            df['Order ID'] = df['Order ID'].astype(str)
            df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce').fillna(0).astype(int)
            
            all_orders.append(df)
            print(f"✅ 已读取马来订单文件: {Path(file_path).name} ({len(df)} 行)")
        except FileNotFoundError:
            print(f"❌ 马来订单文件不存在: {file_path}")
            raise
        except Exception as e:
            print(f"❌ 读取马来订单文件失败 {file_path}: {e}")
            raise ValueError(f"无法读取马来订单文件 {file_path}: {e}")
    
    if not all_orders:
        raise ValueError("没有成功读取任何马来订单文件")
    
    # 合并所有订单数据
    merged_orders = pd.concat(all_orders, ignore_index=True)
    print(f"📋 马来订单数据合并完成: 总计 {len(merged_orders)} 行")
    
    return merged_orders

def merge_settlement_files_mal(settlement_files: List[Union[str, Path]]) -> pd.DataFrame:
    """合并多个马来结算表文件"""
    all_settlements = []
    
    for file_path in settlement_files:
        try:
            df = pd.read_excel(file_path)
            df.columns = df.columns.str.strip()
            
            # 过滤 Type 为 order 的记录
            if 'Type' in df.columns:
                df = df[df['Type'].astype(str).str.lower() == 'order']
            
            df['Order/adjustment ID'] = df['Order/adjustment ID'].astype(str)
            
            all_settlements.append(df)
            print(f"✅ 已读取马来结算文件: {Path(file_path).name} ({len(df)} 行)")
        except FileNotFoundError:
            print(f"❌ 马来结算文件不存在: {file_path}")
            raise
        except Exception as e:
            print(f"❌ 读取马来结算文件失败 {file_path}: {e}")
            raise ValueError(f"无法读取马来结算文件 {file_path}: {e}")
    
    if not all_settlements:
        raise ValueError("没有成功读取任何马来结算文件")
    
    # 合并所有结算数据
    merged_settlements = pd.concat(all_settlements, ignore_index=True)
    print(f"💳 马来结算数据合并完成: 总计 {len(merged_settlements)} 行")
    
    return merged_settlements

def process_malaysia_financial_data(order_files: List[Union[str, Path]], 
                                  settlement_files: List[Union[str, Path]], 
                                  consumption_file: Union[str, Path],
                                  output_dir: Union[str, Path] = ".") -> Path:
    """
    处理马来跨境店财务数据分析
    
    Args:
        order_files: 订单文件列表
        settlement_files: 结算文件列表  
        consumption_file: 产品消耗文件
        output_dir: 输出目录
        
    Returns:
        输出文件路径
    """
    
    print("🚀 开始马来跨境店财务数据分析...")
    
    # -------- 1) 读取订单表（跳过第 2 行注释） --------
    order_df = merge_order_files_mal(order_files)
    
    # -------- 2) 读取结算表并合并结算金额 --------
    sett_df = merge_settlement_files_mal(settlement_files)
    
    order_df = (order_df
                .merge(sett_df[['Order/adjustment ID', 'Total settlement amount']],
                       left_on='Order ID', right_on='Order/adjustment ID', how='left')
                .drop(columns=['Order/adjustment ID']))
    order_df['Total settlement amount'] = pd.to_numeric(order_df['Total settlement amount'],
                                                       errors='coerce').fillna(0)
    
    # -------- 3) 标记出库 / 签收 / 取消 --------
    order_df['is_shipped'] = order_df['Shipped Time'].notna() & \
                             (order_df['Shipped Time'].astype(str).str.strip() != '')
    status_lower = order_df['Order Status'].astype(str).str.lower()
    order_df['is_signed']          = status_lower.isin(['completed', 'delivered'])
    order_df['is_cancelled']       = status_lower == 'canceled'
    order_df['cancel_before_ship'] = order_df['is_cancelled'] & ~order_df['is_shipped']
    order_df['cancel_after_ship']  = order_df['is_cancelled'] &  order_df['is_shipped']
    
    # -------- 4) 计算操作费（未出库 = 0） --------
    order_df['操作费'] = np.where(order_df['is_shipped'],
                               order_df['Seller SKU'].map(OP_FEE).fillna(OP_FEE.get('default', 2.5)), 0.0)
    
    order_df['shipped_qty'] = np.where(order_df['is_shipped'], order_df['Quantity'], 0)
    order_df['signed_qty']  = np.where(order_df['is_signed'],  order_df['Quantity'], 0)
    
    # -------- 5) SKU 层汇总（基础指标） --------
    sku = (order_df
           .groupby('Seller SKU', as_index=False)
           .agg(总结算金额      = ('Total settlement amount', 'sum'),
                总操作费      = ('操作费', 'sum'),
                订单数        = ('Order ID', 'count'),
                出库订单数    = ('is_shipped', 'sum'),
                签收订单数    = ('is_signed', 'sum'),
                出库sku数    = ('shipped_qty', 'sum'),
                签收sku数    = ('signed_qty', 'sum'),
                出库前取消订单 = ('cancel_before_ship', 'sum'),
                出库后取消订单 = ('cancel_after_ship', 'sum')))
    sku['签收率']      = sku['签收订单数'] / sku['订单数']
    sku['出库前取消率'] = sku['出库前取消订单'] / sku['订单数']
    sku['出库后取消率'] = sku['出库后取消订单'] / sku['订单数']
    
    # -------- 6) 合并产品消耗成本表 --------
    cost = pd.read_excel(consumption_file)
    cost.columns = cost.columns.str.strip()
    print(f"📊 已读取产品消耗文件: {Path(consumption_file).name} ({len(cost)} 行)")
    
    # 动态识别列名
    sku_col   = 'Seller SKU' if 'Seller SKU' in cost.columns else 'seller sku'
    unit_col  = '单sku马来币成本' if '单sku马来币成本' in cost.columns else '马来币单sku成本'
    
    cost_sub = (cost[[sku_col, unit_col, '马来币ads消耗', '马来币gmvmax消耗']]
                .rename(columns={sku_col: 'Seller SKU', unit_col: '单sku马来币成本'}))
    cost_sub[['单sku马来币成本', '马来币ads消耗', '马来币gmvmax消耗']] = \
        cost_sub[['单sku马来币成本', '马来币ads消耗', '马来币gmvmax消耗']].apply(
            pd.to_numeric, errors='coerce').fillna(0)
    
    sku = (sku.merge(cost_sub, on='Seller SKU', how='left')
              .fillna({'单sku马来币成本': 0, '马来币ads消耗': 0, '马来币gmvmax消耗': 0}))
    
    # -------- 7) 利润相关指标 --------
    sku['sku产品成本']   = sku['出库sku数'] * sku['单sku马来币成本']
    sku['马来币操作费'] = sku['总操作费'] * MYR_PER_RMB
    sku['利润']       = (sku['总结算金额'] - sku['马来币操作费'] - sku['sku产品成本']
                       - sku['马来币ads消耗'] - sku['马来币gmvmax消耗'])
    sku['人民币利润']  = sku['利润'] / MYR_PER_RMB
    sku['毛利率']     = np.where(sku['总结算金额'] != 0, sku['利润'] / sku['总结算金额'], 0)
    sku['每单利润']    = np.where(sku['签收订单数'] != 0, sku['人民币利润'] / sku['签收订单数'], 0)
    
    # -------- 8) 调整订单列顺序 --------
    first_cols = ['Order ID', 'Total settlement amount', '操作费']
    order_df = order_df[first_cols + [c for c in order_df.columns if c not in first_cols]]
    
    # -------- 9) 导出 --------
    output_path = Path(output_dir) / '马来跨境店财务分析结果.xlsx'
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        order_df.to_excel(writer, sheet_name='订单表_含结算金额和操作费', index=False)
        sku.to_excel(writer, sheet_name='sku总结算金额和操作费', index=False)
        cost.to_excel(writer, sheet_name='产品消耗成本表', index=False)
    
    print(f'✔ 马来跨境店分析完成 → {output_path}')
    return output_path
