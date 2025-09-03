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
from typing import List, Union, Optional, Dict
import re

# === 文件路径 ===
orders_path     = '马7-1.1至4.30订单.xlsx'          # 订单表（第 2 行为注释）
settlement_path = '马七 下 income_20250530073840.xlsx'  # 结算表
cost_path       = '产品成本消耗表.xlsx'              # 产品成本消耗表
output_path     = '订单_汇总_成本利润.xlsx'

# 出库订单固定操作费（人民币）
# 注意：单位是人民币（RMB）。仅在成本表未提供“订单操作费”(人民币)时作为后备值使用。
OP_FEE_FALLBACK = {'xifashui': 2.5, 'kingstick': 2.5}

# ---------------- 通用SKU解析/规格化工具（与印尼模块一致） ----------------
def _parse_sku_multiplier_mal(raw_sku: str) -> tuple[str, int]:
    if raw_sku is None or (isinstance(raw_sku, float) and pd.isna(raw_sku)):
        return ("", 1)
    s = str(raw_sku).strip().lower().replace(" ", "")
    if not s:
        return ("", 1)
    m = re.match(r"^(?P<base>.+?)[\-\*xX×](?P<num>\d+)$", s)
    if m:
        base = m.group("base").strip("-*")
        num = int(m.group("num")) if m.group("num") else 1
        return (base, max(num, 1))
    m2 = re.match(r"^(?P<base>[a-zA-Z\u4e00-\u9fa5_\-/]+?)(?P<num>\d+)$", s)
    if m2:
        base = m2.group("base")
        num = int(m2.group("num")) if m2.group("num") else 1
        return (base, max(num, 1))
    if s.endswith(("-1", "*1", "x1", "×1")):
        return (s[:-2].rstrip("-*") or s, 1)
    return (s, 1)

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
            # 规格化 SKU 并放大量：Seller SKU 可能带 -2/*2/x2/2 尾数
            if 'Seller SKU' in df.columns:
                norm_skus = []
                new_qty = []
                for sku, q in zip(df['Seller SKU'], df['Quantity']):
                    base, mult = _parse_sku_multiplier_mal(sku)
                    norm_skus.append(base)
                    new_qty.append(int(q) * int(mult))
                df['Seller SKU'] = norm_skus
                df['Quantity'] = new_qty
            
            all_orders.append(df)
            print(f"✅ 已读取马来订单文件: {Path(file_path).name} ({len(df)} 行)")
        except Exception as e:
            print(f"❌ 读取马来订单文件失败 {file_path}: {e}")
            raise
    
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
        except Exception as e:
            print(f"❌ 读取马来结算文件失败 {file_path}: {e}")
            raise
    
    if not all_settlements:
        raise ValueError("没有成功读取任何马来结算文件")
    
    # 合并所有结算数据
    merged_settlements = pd.concat(all_settlements, ignore_index=True)
    print(f"💳 马来结算数据合并完成: 总计 {len(merged_settlements)} 行")
    
    return merged_settlements

def process_malaysia_financial_data(order_files: List[Union[str, Path]], 
                                  settlement_files: List[Union[str, Path]], 
                                  consumption_file: Union[str, Path],
                                  output_dir: Union[str, Path] = ".",
                                  local_per_rmb: Optional[float] = None) -> Path:
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

    # 允许外部传入汇率（本币/人民币），默认0.6（马币/人民币）
    rate_local_per_rmb = float(local_per_rmb) if local_per_rmb else 0.6
    
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

    # 用 Delivered Time 判断签收
    order_df['is_signed'] = order_df['Delivered Time'].notna() & \
                            (order_df['Delivered Time'].astype(str).str.strip() != '')

    # 中文"取消"关键词；保留英文以兼容多语言文件
    status_raw = order_df['Order Status'].astype(str)
    order_df['is_cancelled'] = status_raw.str.contains('取消', na=False) | \
                               status_raw.str.lower().eq('canceled')
    order_df['cancel_before_ship'] = order_df['is_cancelled'] & ~order_df['is_shipped']
    order_df['cancel_after_ship']  = order_df['is_cancelled'] &  order_df['is_shipped']
    
    # -------- 4) 读取产品消耗成本表，并确定操作费来源 --------
    cost = pd.read_excel(consumption_file)
    cost.columns = cost.columns.str.strip()
    print(f"📊 已读取产品消耗文件: {Path(consumption_file).name} ({len(cost)} 行)")
    
    # 动态识别列名
    sku_col   = 'Seller SKU' if 'Seller SKU' in cost.columns else 'seller sku'
    unit_col  = '单sku马来币成本' if '单sku马来币成本' in cost.columns else '马来币单sku成本'
    # 订单操作费列（单位：人民币 RMB；若缺失则使用后备映射）
    op_fee_candidates = ['订单操作费', '订单操作费_RMB', '人民币订单操作费', '操作费']
    op_fee_col = next((c for c in op_fee_candidates if c in cost.columns), None)
    
    # 若成本表缺少特定前缀列，尝试按后缀匹配并重命名到马来币前缀
    def _find_col_by_suffix(df: pd.DataFrame, suffix: str) -> Optional[str]:
        for col in df.columns:
            if isinstance(col, str) and col.strip().endswith(suffix):
                return col
        return None

    if '马来币ads消耗' not in cost.columns:
        c = _find_col_by_suffix(cost, 'ads消耗')
        if c:
            cost = cost.rename(columns={c: '马来币ads消耗'})
    if '马来币gmvmax消耗' not in cost.columns:
        c = _find_col_by_suffix(cost, 'gmvmax消耗')
        if c:
            cost = cost.rename(columns={c: '马来币gmvmax消耗'})

    keep_cols = [sku_col, unit_col, '马来币ads消耗', '马来币gmvmax消耗'] + ([op_fee_col] if op_fee_col else [])
    # 如果成本表包含产品名列“产品”，保留以用于展示
    if '产品' in cost.columns:
        keep_cols.append('产品')
    cost_sub = (cost[keep_cols]
                .rename(columns={sku_col: 'Seller SKU', unit_col: '单sku马来币成本',
                                 (op_fee_col if op_fee_col else '订单操作费'): '订单操作费'}))
    for col in ['单sku马来币成本', '马来币ads消耗', '马来币gmvmax消耗', '订单操作费']:
        if col in cost_sub.columns:
            cost_sub[col] = pd.to_numeric(cost_sub[col], errors='coerce').fillna(0)
    # 计算订单级操作费（未出库=0；优先用表格里的“订单操作费”）
    if '订单操作费' in cost_sub.columns:
        op_fee_map = cost_sub.set_index('Seller SKU')['订单操作费']
        order_df['操作费'] = np.where(order_df['is_shipped'],
                                   order_df['Seller SKU'].map(op_fee_map).fillna(0), 0.0)
    else:
        order_df['操作费'] = np.where(order_df['is_shipped'],
                                   order_df['Seller SKU'].map(OP_FEE_FALLBACK).fillna(0), 0.0)

    # -------- 5) 数量辅助列 --------
    order_df['shipped_qty'] = np.where(order_df['is_shipped'], order_df['Quantity'], 0)
    order_df['signed_qty']  = np.where(order_df['is_signed'],  order_df['Quantity'], 0)

    # -------- 6) SKU 层汇总（基础指标） --------
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

    # 合并成本消耗子表
    sku = (sku.merge(cost_sub, on='Seller SKU', how='left'))
    # 仅对数值列填充0，避免把“产品”填为0
    for col in ['单sku马来币成本', '马来币ads消耗', '马来币gmvmax消耗']:
        if col in sku.columns:
            sku[col] = sku[col].fillna(0)

    # -------- 7) 利润相关指标 --------
    sku['sku产品成本']   = sku['出库sku数'] * sku['单sku马来币成本']
    # 将人民币操作费按“本币/人民币”汇率折算为本币
    sku['马来币操作费'] = sku['总操作费'] * rate_local_per_rmb
    sku['利润']       = (sku['总结算金额'] - sku['马来币操作费'] - sku['sku产品成本']
                       - sku['马来币ads消耗'] - sku['马来币gmvmax消耗'])
    # 按“本币/人民币”汇率折算回人民币
    sku['人民币利润']  = sku['利润'] / rate_local_per_rmb
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


def _detect_name_col_mal(df: pd.DataFrame) -> Optional[str]:
    candidates_exact = ["Product Name", "Item Name", "Title", "Name", "产品名称", "商品名称", "产品名"]
    for col in df.columns:
        if col in candidates_exact:
            return col
    for col in df.columns:
        lc = str(col).lower()
        if any(k in lc for k in ["name", "title", "名称", "商品", "产品"]):
            return col
    return None


def compute_malaysia_summary(order_files: List[Union[str, Path]],
                             settlement_files: List[Union[str, Path]],
                             consumption_file: Union[str, Path],
                             local_per_rmb: Optional[float] = None) -> pd.DataFrame:
    """
    计算马来模块的SKU级摘要，用于前端渲染。
    返回列：产品名, sku, 订单量, 签收率, 人民币利润, 每单利润, 毛利润率
    """
    # 读取订单
    rate_local_per_rmb = float(local_per_rmb) if local_per_rmb else 0.6
    order_df = merge_order_files_mal(order_files)
    # 读取结算
    sett_df = merge_settlement_files_mal(settlement_files)
    order_df = (order_df
                .merge(sett_df[['Order/adjustment ID', 'Total settlement amount']],
                       left_on='Order ID', right_on='Order/adjustment ID', how='left')
                .drop(columns=['Order/adjustment ID']))
    order_df['Total settlement amount'] = pd.to_numeric(order_df['Total settlement amount'], errors='coerce').fillna(0)

    # 统一SKU格式
    if 'Seller SKU' in order_df.columns:
        order_df['Seller SKU'] = order_df['Seller SKU'].astype(str).str.strip()
    
    # 出库/签收/取消
    order_df['is_shipped'] = order_df['Shipped Time'].notna() & (order_df['Shipped Time'].astype(str).str.strip() != '')
    order_df['is_signed']  = order_df['Delivered Time'].notna() & (order_df['Delivered Time'].astype(str).str.strip() != '')
    status_raw = order_df['Order Status'].astype(str)
    order_df['is_cancelled'] = status_raw.str.contains('取消', na=False) | status_raw.str.lower().eq('canceled')
    order_df['cancel_before_ship'] = order_df['is_cancelled'] & ~order_df['is_shipped']
    order_df['cancel_after_ship']  = order_df['is_cancelled'] &  order_df['is_shipped']

    # 成本表
    cost = pd.read_excel(consumption_file)
    # 去除列名中的前后空白与BOM
    cost.columns = [str(c).replace('\ufeff','').replace('\u200b','').strip() for c in cost.columns]
    # 产品列（若未找到“产品”，则回退为第一列）
    prod_col = '产品' if '产品' in cost.columns else (cost.columns[0] if len(cost.columns) > 0 else None)
    sku_col = 'Seller SKU' if 'Seller SKU' in cost.columns else 'seller sku'
    unit_col = '单sku马来币成本' if '单sku马来币成本' in cost.columns else '马来币单sku成本'
    op_fee_candidates = ['订单操作费', '订单操作费_RMB', '人民币订单操作费', '操作费']
    op_fee_col = next((c for c in op_fee_candidates if c in cost.columns), None)
    # 后缀匹配归一化ads/gmvmax列到马来币前缀
    def _find_col_by_suffix(df: pd.DataFrame, suffix: str) -> Optional[str]:
        for col in df.columns:
            if isinstance(col, str) and col.strip().endswith(suffix):
                return col
        return None
    if '马来币ads消耗' not in cost.columns:
        c = _find_col_by_suffix(cost, 'ads消耗')
        if c:
            cost = cost.rename(columns={c: '马来币ads消耗'})
    if '马来币gmvmax消耗' not in cost.columns:
        c = _find_col_by_suffix(cost, 'gmvmax消耗')
        if c:
            cost = cost.rename(columns={c: '马来币gmvmax消耗'})
    keep_cols = [sku_col, unit_col, '马来币ads消耗', '马来币gmvmax消耗'] + ([op_fee_col] if op_fee_col else [])
    # 把产品列也带上用于展示
    if prod_col and prod_col not in keep_cols:
        keep_cols.append(prod_col)
    cost_sub = (cost[keep_cols]
                .rename(columns={sku_col: 'Seller SKU', unit_col: '单sku马来币成本',
                                 (op_fee_col if op_fee_col else '订单操作费'): '订单操作费'}))
    # 统一产品列名为“产品”
    if '产品' not in cost_sub.columns and prod_col and prod_col in cost_sub.columns:
        cost_sub = cost_sub.rename(columns={prod_col: '产品'})
    for col in ['单sku马来币成本', '马来币ads消耗', '马来币gmvmax消耗', '订单操作费']:
        if col in cost_sub.columns:
            cost_sub[col] = pd.to_numeric(cost_sub[col], errors='coerce').fillna(0)
    # 统一成本表SKU格式并规格化到基础SKU
    cost_sub['Seller SKU'] = cost_sub['Seller SKU'].astype(str).str.strip().str.lower()
    cost_sub['Seller SKU'] = cost_sub['Seller SKU'].map(lambda s: _parse_sku_multiplier_mal(s)[0])

    # 操作费
    if '订单操作费' in cost_sub.columns:
        op_fee_map = cost_sub.set_index('Seller SKU')['订单操作费']
        order_df['操作费'] = np.where(order_df['is_shipped'], order_df['Seller SKU'].map(op_fee_map).fillna(0), 0.0)
    else:
        order_df['操作费'] = np.where(order_df['is_shipped'], order_df['Seller SKU'].map(OP_FEE_FALLBACK).fillna(0), 0.0)

    order_df['shipped_qty'] = np.where(order_df['is_shipped'], order_df['Quantity'], 0)
    order_df['signed_qty']  = np.where(order_df['is_signed'],  order_df['Quantity'], 0)

    sku = (order_df
           .groupby('Seller SKU', as_index=False)
           .agg(总结算金额=('Total settlement amount', 'sum'),
                总操作费=('操作费', 'sum'),
                订单数=('Order ID', 'count'),
                出库订单数=('is_shipped', 'sum'),
                签收订单数=('is_signed', 'sum'),
                出库sku数=('shipped_qty', 'sum'),
                签收sku数=('signed_qty', 'sum'),
                出库前取消订单=('cancel_before_ship', 'sum'),
                出库后取消订单=('cancel_after_ship', 'sum')))
    sku['签收率'] = sku['签收订单数'] / sku['订单数']

    # 合并成本
    sku = (sku.merge(cost_sub, on='Seller SKU', how='left')
              .fillna({'单sku马来币成本': 0, '马来币ads消耗': 0, '马来币gmvmax消耗': 0}))

    # 利润
    sku['sku产品成本'] = sku['出库sku数'] * sku['单sku马来币成本']
    sku['马来币操作费'] = sku['总操作费'] * rate_local_per_rmb
    sku['利润'] = (sku['总结算金额'] - sku['马来币操作费'] - sku['sku产品成本']
                - sku['马来币ads消耗'] - sku['马来币gmvmax消耗'])
    sku['人民币利润'] = sku['利润'] / rate_local_per_rmb
    sku['毛利率'] = np.where(sku['总结算金额'] != 0, sku['利润'] / sku['总结算金额'], 0)
    sku['每单利润'] = np.where(sku['签收订单数'] != 0, sku['人民币利润'] / sku['签收订单数'], 0)

    # 产品名
    # 直接从成本表“产品”列取产品名
    if '产品' in sku.columns:
        sku['产品名'] = sku['产品'].astype(str)
    else:
        sku['产品名'] = ''

    out = sku[['Seller SKU', '产品名', '订单数', '签收订单数', '总结算金额', '利润', '签收率', '人民币利润', '每单利润', '毛利率']].copy()
    out = out.rename(columns={'Seller SKU': 'sku', '订单数': '订单量', '毛利率': '毛利润率'})
    # 前端汇总需要的统一字段
    out['毛利率分子'] = out['利润']       # 本币（马来币）
    out['毛利率分母'] = out['总结算金额']  # 本币（马来币）
    # 排序
    for col in ['签收率', '人民币利润', '每单利润', '毛利润率']:
        out[col] = pd.to_numeric(out[col], errors='coerce')
    out = out.fillna({'签收率': 0, '毛利润率': 0, '每单利润': 0, '人民币利润': 0,
                      '签收订单数': 0, '总结算金额': 0, '利润': 0, '毛利率分子': 0, '毛利率分母': 0})
    out = out[['产品名', 'sku', '订单量', '签收率', '人民币利润', '每单利润', '毛利润率',
               '签收订单数', '毛利率分子', '毛利率分母']]
    out = out.sort_values(by='订单量', ascending=False, kind='mergesort').reset_index(drop=True)
    return out
