#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analysis_multi.py
------------------------------------------------
支持多文件处理的财务数据分析模块
- 支持多个订单表文件合并
- 支持多个结算表文件合并
- 单个产品消耗表
- 支持组合SKU预处理
"""

import pandas as pd
from pathlib import Path
from typing import List, Union, Optional, Dict

from sku_utils import preprocess_combo_sku

# 默认汇率设置（可通过函数参数覆盖）
# 仅保留印尼盾/人民币汇率，已移除美元相关
IDR_PER_RMB = 2300

def merge_order_files(order_files: List[Union[str, Path]]) -> pd.DataFrame:
    """合并多个订单表文件"""
    all_orders = []
    
    for file_path in order_files:
        try:
            df = pd.read_excel(file_path, dtype=str)
            # 标准化第一列为order_id
            df = df.rename(columns={df.columns[0]: "order_id"})
            all_orders.append(df)
            print(f"✅ 已读取订单文件: {Path(file_path).name} ({len(df)} 行)")
        except Exception as e:
            print(f"❌ 读取订单文件失败 {file_path}: {e}")
            raise
    
    if not all_orders:
        raise ValueError("没有成功读取任何订单文件")
    
    # 合并所有订单数据
    merged_orders = pd.concat(all_orders, ignore_index=True)
    print(f"📋 订单数据合并完成: 总计 {len(merged_orders)} 行")
    
    return merged_orders

def merge_settlement_files(settlement_files: List[Union[str, Path]]) -> pd.DataFrame:
    """合并多个结算表文件"""
    all_settlements = []
    
    for file_path in settlement_files:
        try:
            df = pd.read_excel(file_path, dtype=str)
            # 标准化第一列为order_id
            df = df.rename(columns={df.columns[0]: "order_id"})
            
            # 查找结算金额列
            settlement_col = None
            for col in df.columns:
                if "settlement" in col.lower():
                    settlement_col = col
                    break
            
            if settlement_col and settlement_col != "Total settlement amount":
                df = df.rename(columns={settlement_col: "Total settlement amount"})
            
            all_settlements.append(df)
            print(f"✅ 已读取结算文件: {Path(file_path).name} ({len(df)} 行)")
        except Exception as e:
            print(f"❌ 读取结算文件失败 {file_path}: {e}")
            raise
    
    if not all_settlements:
        raise ValueError("没有成功读取任何结算文件")
    
    # 合并所有结算数据
    merged_settlements = pd.concat(all_settlements, ignore_index=True)
    print(f"💳 结算数据合并完成: 总计 {len(merged_settlements)} 行")
    
    return merged_settlements

def process_financial_data(order_files: List[Union[str, Path]], 
                         settlement_files: List[Union[str, Path]], 
                         consumption_file: Union[str, Path],
                         output_dir: Union[str, Path] = ".",
                         idr_per_rmb: Optional[float] = None) -> Path:
    """
    处理财务数据分析
    
    Args:
        order_files: 订单文件列表
        settlement_files: 结算文件列表  
        consumption_file: 产品消耗文件
        output_dir: 输出目录
        
    Returns:
        输出文件路径
    """
    
    print("🚀 开始财务数据分析...")

    # 使用传入的汇率（如有），否则使用默认值
    local_idr_per_rmb = float(idr_per_rmb) if idr_per_rmb else IDR_PER_RMB
    
    # -------- 读取和合并文件 --------
    order = merge_order_files(order_files)
    settle = merge_settlement_files(settlement_files)
    cons = pd.read_excel(consumption_file, dtype=str)
    print(f"📊 已读取产品消耗文件: {Path(consumption_file).name} ({len(cons)} 行)")

    # -------- 数据预处理 --------
    # 处理结算金额
    if "Total settlement amount" not in settle.columns:
        settlement_cols = [c for c in settle.columns if "settlement" in c.lower()]
        if settlement_cols:
            settle = settle.rename(columns={settlement_cols[0]: "Total settlement amount"})
        else:
            raise ValueError("结算表中找不到结算金额列")
    
    settle["Total settlement amount"] = pd.to_numeric(settle["Total settlement amount"], errors="coerce")

    # 处理重复订单
    dup_settle = settle[settle.duplicated("order_id", keep=False)]
    settle = settle.drop_duplicates("order_id", keep=False)
    print(f"⚠️  排除重复结算订单: {len(dup_settle)} 行")

    # 合并订单和结算数据
    order = order.merge(settle[["order_id","Total settlement amount"]], on="order_id", how="left")

    # 识别关键列
    qty_col = None
    sku_col = None
    ship_col = None
    status_col = None
    
    for col in order.columns:
        if "数量" in col and qty_col is None:
            qty_col = col
        elif "sku" in col.lower() and sku_col is None:
            sku_col = col
        elif "是否出库" in col and ship_col is None:
            ship_col = col
        elif "平台状态" in col and status_col is None:
            status_col = col
    
    if not all([qty_col, sku_col, ship_col, status_col]):
        missing = []
        if not qty_col: missing.append("数量列")
        if not sku_col: missing.append("SKU列")
        if not ship_col: missing.append("是否出库列")
        if not status_col: missing.append("平台状态列")
        raise ValueError(f"订单表中缺少必要列: {', '.join(missing)}")

    print(f"📝 识别到关键列: 数量({qty_col}), SKU({sku_col}), 出库({ship_col}), 状态({status_col})")

    # 数据类型转换（必须在组合SKU预处理之前进行）
    order[qty_col] = pd.to_numeric(order[qty_col], errors="coerce").fillna(0).astype(int)

    # -------- 组合SKU预处理 --------
    print("🔧 开始组合SKU预处理...")
    order = preprocess_combo_sku(order, sku_col, qty_col)

    # 继续其他数据转换
    order["_shipped"] = order[ship_col].str.strip().str.lower()
    order["_status"] = order[status_col].str.strip().str.lower()

    # 计算每行结算金额和操作费
    lines = order.groupby("order_id")["order_id"].transform("size")
    order["settlement_per_line"] = order["Total settlement amount"] / lines

    # 运营费用计算
    tot_qty = order.groupby("order_id")[qty_col].transform("sum")
    order["order_fee_rmb"] = [
        2.0 if (s=="yes" and q==1) else 2.5 if (s=="yes" and q>1) else 0.0
        for s,q in zip(order["_shipped"], tot_qty)
    ]
    order["operation_fee_per_line_rmb"] = order.groupby("order_id")["order_fee_rmb"].transform("max") / lines

    # -------- SKU级别聚合 --------
    pair_df = order[[sku_col,"order_id","_shipped","_status"]].drop_duplicates([sku_col,"order_id"])

    # 订单级计数
    metrics = {
        "订单数": pair_df.groupby(sku_col)["order_id"].nunique(),
        "出库订单数数量": pair_df[pair_df["_shipped"]=="yes"].groupby(sku_col)["order_id"].nunique(),
        "签收订单数": pair_df[pair_df["_status"].isin(["delivered","completed"])]\
                     .groupby(sku_col)["order_id"].nunique(),
        "取消订单数": pair_df[pair_df["_status"]=="cancelled"].groupby(sku_col)["order_id"].nunique(),
        "出库前取消订单数": pair_df[(pair_df["_status"]=="cancelled") & (pair_df["_shipped"]=="no")]\
                         .groupby(sku_col)["order_id"].nunique(),
        "出库后取消订单数": pair_df[(pair_df["_status"]=="cancelled") & (pair_df["_shipped"]=="yes")]\
                         .groupby(sku_col)["order_id"].nunique(),
        "仍在途订单数": pair_df[pair_df["_status"]=="in transit"].groupby(sku_col)["order_id"].nunique(),
    }

    # 金额 & 数量聚合
    shipped_order = order[order["_shipped"] == "yes"]
    delivered_order = order[order["_status"].isin(["delivered","completed"])]
    
    base = order.groupby(sku_col).agg(
        sku_total_settlement    = ("settlement_per_line", "sum"),
        sku_total_operation_fee = ("operation_fee_per_line_rmb", "sum")
    )
    
    # 出库数量
    shipped_qty = shipped_order.groupby(sku_col)[qty_col].sum()
    base = base.join(shipped_qty.rename("出库数量"), how="left")
    
    # 签收金额  
    delivered_amount = delivered_order.groupby(sku_col)["settlement_per_line"].sum()
    base = base.join(delivered_amount.rename("签收金额"), how="left")

    sku = base
    for k,v in metrics.items(): 
        sku = sku.join(v.rename(k), how="left")
    sku = sku.fillna(0)

    # 运营率计算
    sku["签收率"] = sku["签收订单数"] / sku["订单数"]
    sku["取消率"] = sku["取消订单数"] / sku["订单数"]
    sku["出库前取消率"] = sku["出库前取消订单数"] / sku["订单数"]
    sku["出库后取消率"] = sku["出库后取消订单数"] / sku["订单数"]
    sku["仍在途率"] = sku["仍在途订单数"] / sku["订单数"]
    sku = sku.drop(columns=["取消订单数","出库前取消订单数","出库后取消订单数","仍在途订单数"])

    # -------- 产品消耗数据处理 --------
    if sku_col not in cons.columns:
        cons = cons.rename(columns={cons.columns[0]: sku_col})
    
    # 数值列转换
    for c in cons.columns:
        if c != sku_col: 
            cons[c] = pd.to_numeric(cons[c], errors="coerce")

    # 若未找到特定前缀列，尝试通过后缀模式匹配进行归一化
    def _find_col_by_suffix(df: pd.DataFrame, suffix: str) -> Optional[str]:
        for col in df.columns:
            if isinstance(col, str) and col.strip().endswith(suffix):
                return col
        return None

    # 将任意“xxxads消耗/xxxgmvmax消耗/xxx单sku成本”映射为印尼盾前缀，以便后续统一处理
    if "印尼盾ads消耗" not in cons.columns:
        c = _find_col_by_suffix(cons, "ads消耗")
        if c:
            cons = cons.rename(columns={c: "印尼盾ads消耗"})
    if "印尼盾gmvmax消耗" not in cons.columns:
        c = _find_col_by_suffix(cons, "gmvmax消耗")
        if c:
            cons = cons.rename(columns={c: "印尼盾gmvmax消耗"})
    if "印尼盾单sku成本" not in cons.columns:
        # 兼容“单sku印尼盾成本/印尼盾单sku成本/xxx单sku成本”
        candidates = ["印尼盾单sku成本", "单sku印尼盾成本"]
        hit = next((c for c in candidates if c in cons.columns), None)
        if hit:
            cons = cons.rename(columns={hit: "印尼盾单sku成本"})
        else:
            c = _find_col_by_suffix(cons, "单sku成本")
            if c:
                cons = cons.rename(columns={c: "印尼盾单sku成本"})

    # 确保必要列存在
    for col in ["印尼盾ads消耗","印尼盾gmvmax消耗","印尼盾单sku成本"]:
        if col not in cons.columns: 
            cons[col] = 0.0

    # 货币转换（按传入/默认汇率）
    cons["人民币单sku成本"] = cons["印尼盾单sku成本"] / local_idr_per_rmb

    # 合并消耗数据
    keep = [sku_col, "印尼盾ads消耗", "印尼盾gmvmax消耗", "印尼盾单sku成本", "人民币单sku成本"]
    sku = sku.merge(cons[keep], on=sku_col, how="left").fillna(0)

    # -------- 财务指标计算 --------
    sku["印尼盾操作费"] = sku["sku_total_operation_fee"] * local_idr_per_rmb
    sku["印尼盾消耗"] = sku["印尼盾ads消耗"] + sku["印尼盾gmvmax消耗"]
    sku["印尼盾产品成本"] = sku["印尼盾单sku成本"] * sku["出库数量"]

    sku["利润"] = sku["sku_total_settlement"] - sku["印尼盾操作费"] - sku["印尼盾产品成本"] - sku["印尼盾消耗"]
    sku["人民币利润"] = sku["利润"] / local_idr_per_rmb
    sku["签收毛利率"] = sku["利润"] / sku["签收金额"].replace(0, pd.NA)
    sku["每单利润"] = sku["人民币利润"] / sku["签收订单数"].replace(0, pd.NA)

    # -------- 输出结果 --------
    output_path = Path(output_dir) / "财务分析结果_多文件.xlsx"
    
    with pd.ExcelWriter(output_path, engine="openpyxl") as w:
        # 订单表（含结算与操作费）
        order.to_excel(w, sheet_name="订单表_含结算与操作费", index=False)
        
        # SKU汇总（结算与操作费）
        sku[["sku_total_settlement","sku_total_operation_fee"]].reset_index()\
           .to_excel(w, sheet_name="sku汇总_结算与操作费", index=False)
        
        # 排除的重复订单
        if len(dup_settle) > 0:
            dup_settle.to_excel(w, sheet_name="排除订单_多行结算", index=False)
        
        # SKU财务指标
        cols = sku.columns.tolist()
        if "印尼盾操作费" in cols:
            # 将印尼盾操作费移到前面
            cols.insert(3, cols.pop(cols.index("印尼盾操作费")))
        sku[cols].reset_index().to_excel(w, sheet_name="sku财务指标", index=False)
    
    print(f"✅ 分析完成! 结果已保存到: {output_path}")
    print(f"📈 处理了 {len(order_files)} 个订单文件, {len(settlement_files)} 个结算文件")
    print(f"📊 总计订单: {len(order)} 行, SKU数量: {len(sku)} 个")
    
    return output_path


def _detect_product_name_column(df: pd.DataFrame) -> Optional[str]:
    """
    在订单或成本表中尝试识别产品名称列名。
    优先匹配常见的中文/英文列名。
    """
    if df is None or df.empty:
        return None

    candidates_exact = [
        "产品名称", "商品名称", "产品名", "品名",
        "Product Name", "Item Name", "Title", "Name"
    ]
    for col in df.columns:
        if col in candidates_exact:
            return col

    # 次优先：包含“名称/商品/产品”的列
    candidates_contains = ["名称", "商品", "产品", "name", "title"]
    lower_cols = {c.lower(): c for c in df.columns}
    for key in candidates_contains:
        for lc, orig in lower_cols.items():
            if key in lc:
                return orig
    return None


def _build_sku_name_map(order_df: pd.DataFrame, sku_col: str, cons_df: Optional[pd.DataFrame] = None) -> Dict[str, str]:
    """
    从订单表和可选的消耗表中，构建 sku -> 产品名 的映射。
    优先使用订单表中出现频率最高的产品名；若无则尝试消耗表。
    """
    name_map: Dict[str, str] = {}

    # 1) 从订单表提取
    name_col = _detect_product_name_column(order_df)
    if name_col:
        tmp = (
            order_df[[sku_col, name_col]]
            .dropna()
            .astype({sku_col: str})
        )
        if not tmp.empty:
            mode_name = (
                tmp.groupby(sku_col)[name_col]
                   .agg(lambda s: s.value_counts().index[0])
            )
            name_map.update(mode_name.to_dict())

    # 2) 从消耗表补充
    if cons_df is not None and sku_col in cons_df.columns:
        cons_name_col = _detect_product_name_column(cons_df)
        if cons_name_col:
            ctmp = cons_df[[sku_col, cons_name_col]].dropna().astype({sku_col: str})
            for k, v in ctmp.values:
                name_map.setdefault(str(k), str(v))

    return name_map


def compute_indonesia_summary(order_files: List[Union[str, Path]],
                              settlement_files: List[Union[str, Path]],
                              consumption_file: Union[str, Path],
                              idr_per_rmb: Optional[float] = None) -> pd.DataFrame:
    """
    计算印尼模块的SKU级摘要，用于前端渲染。
    返回列：产品名, sku, 订单量, 签收率, 人民币利润, 每单利润, 毛利润率
    """
    # 使用传入的汇率（如有），否则使用默认值
    local_idr_per_rmb = float(idr_per_rmb) if idr_per_rmb else IDR_PER_RMB

    # 读取与合并（沿用主流程逻辑）
    order = merge_order_files(order_files)
    settle = merge_settlement_files(settlement_files)
    cons = pd.read_excel(consumption_file, dtype=str)

    if "Total settlement amount" not in settle.columns:
        settlement_cols = [c for c in settle.columns if "settlement" in c.lower()]
        if settlement_cols:
            settle = settle.rename(columns={settlement_cols[0]: "Total settlement amount"})
        else:
            raise ValueError("结算表中找不到结算金额列")
    settle["Total settlement amount"] = pd.to_numeric(settle["Total settlement amount"], errors="coerce")

    # 排除重复订单
    settle = settle.drop_duplicates("order_id", keep=False)

    # 合并
    order = order.merge(settle[["order_id", "Total settlement amount"]], on="order_id", how="left")

    # 识别列
    qty_col = None
    sku_col = None
    ship_col = None
    status_col = None
    for col in order.columns:
        if "数量" in col and qty_col is None:
            qty_col = col
        elif "sku" in col.lower() and sku_col is None:
            sku_col = col
        elif "是否出库" in col and ship_col is None:
            ship_col = col
        elif "平台状态" in col and status_col is None:
            status_col = col
    if not all([qty_col, sku_col, ship_col, status_col]):
        missing = []
        if not qty_col: missing.append("数量列")
        if not sku_col: missing.append("SKU列")
        if not ship_col: missing.append("是否出库列")
        if not status_col: missing.append("平台状态列")
        raise ValueError(f"订单表中缺少必要列: {', '.join(missing)}")

    order[qty_col] = pd.to_numeric(order[qty_col], errors="coerce").fillna(0).astype(int)

    # 统一SKU值格式
    order[sku_col] = order[sku_col].astype(str).str.strip()

    # 组合SKU预处理
    order = preprocess_combo_sku(order, sku_col, qty_col)

    order["_shipped"] = order[ship_col].str.strip().str.lower()
    order["_status"] = order[status_col].str.strip().str.lower()

    lines = order.groupby("order_id")["order_id"].transform("size")
    order["settlement_per_line"] = order["Total settlement amount"] / lines

    # 运营费用
    tot_qty = order.groupby("order_id")[qty_col].transform("sum")
    order["order_fee_rmb"] = [
        2.0 if (s == "yes" and q == 1) else 2.5 if (s == "yes" and q > 1) else 0.0
        for s, q in zip(order["_shipped"], tot_qty)
    ]
    order["operation_fee_per_line_rmb"] = order.groupby("order_id")["order_fee_rmb"].transform("max") / lines

    pair_df = order[[sku_col, "order_id", "_shipped", "_status"]].drop_duplicates([sku_col, "order_id"])
    metrics = {
        "订单数": pair_df.groupby(sku_col)["order_id"].nunique(),
        "签收订单数": pair_df[pair_df["_status"].isin(["delivered", "completed"])].groupby(sku_col)["order_id"].nunique(),
    }

    shipped_order = order[order["_shipped"] == "yes"]
    delivered_order = order[order["_status"].isin(["delivered", "completed"])]

    base = order.groupby(sku_col).agg(
        sku_total_settlement=("settlement_per_line", "sum"),
        sku_total_operation_fee=("operation_fee_per_line_rmb", "sum"),
    )
    shipped_qty = shipped_order.groupby(sku_col)[qty_col].sum()
    base = base.join(shipped_qty.rename("出库数量"), how="left")
    delivered_amount = delivered_order.groupby(sku_col)["settlement_per_line"].sum()
    base = base.join(delivered_amount.rename("签收金额"), how="left")

    sku = base
    for k, v in metrics.items():
        sku = sku.join(v.rename(k), how="left")
    sku = sku.fillna(0)

    sku["签收率"] = sku["签收订单数"] / sku["订单数"].replace(0, pd.NA)

    # 消耗表处理（沿用主流程）
    # 规范消耗表列名，去除空白
    cons.columns = cons.columns.str.strip()
    if sku_col not in cons.columns:
        cons = cons.rename(columns={cons.columns[0]: sku_col})
    cons[sku_col] = cons[sku_col].astype(str).str.strip()
    # 仅将数值类列转为数值，避免将“产品”等文本列转为NaN
    numeric_cols = ["印尼盾ads消耗", "印尼盾gmvmax消耗", "印尼盾单sku成本"]
    for col in numeric_cols:
        if col in cons.columns:
            cons[col] = pd.to_numeric(cons[col], errors="coerce")
    for col in numeric_cols:
        if col not in cons.columns:
            cons[col] = 0.0
    cons["人民币单sku成本"] = cons["印尼盾单sku成本"] / local_idr_per_rmb
    keep = [
        sku_col,
        "印尼盾ads消耗",
        "印尼盾gmvmax消耗",
        "印尼盾单sku成本",
        "人民币单sku成本",
    ]
    # 如果消费表包含产品名列"产品"，一并带上
    if "产品" in cons.columns:
        keep.append("产品")
    sku = sku.merge(cons[keep], on=sku_col, how="left")
    # 仅对数值列填充0，避免把“产品”填充为0
    fill_zero_cols = [c for c in [
        "印尼盾ads消耗","印尼盾gmvmax消耗","印尼盾单sku成本","人民币单sku成本"
    ] if c in sku.columns]
    sku[fill_zero_cols] = sku[fill_zero_cols].fillna(0)

    # 财务指标
    sku["印尼盾操作费"] = sku["sku_total_operation_fee"] * local_idr_per_rmb
    sku["印尼盾消耗"] = sku["印尼盾ads消耗"] + sku["印尼盾gmvmax消耗"]
    sku["印尼盾产品成本"] = sku["印尼盾单sku成本"] * sku["出库数量"]
    sku["利润"] = sku["sku_total_settlement"] - sku["印尼盾操作费"] - sku["印尼盾产品成本"] - sku["印尼盾消耗"]
    sku["人民币利润"] = sku["利润"] / local_idr_per_rmb
    sku["签收毛利率"] = sku["利润"] / sku["签收金额"].replace(0, pd.NA)
    sku["每单利润"] = sku["人民币利润"] / sku["签收订单数"].replace(0, pd.NA)

    # 构建产品名
    sku = sku.reset_index().rename(columns={sku_col: "sku"})
    # 优先从消耗表的“产品”列获取产品名
    if "产品" in sku.columns:
        sku["产品名"] = sku["产品"].astype(str)
    else:
        # 兜底：为空字符串
        sku["产品名"] = ""

    # 选择并重命名列（同时保留汇总需要的隐含字段）
    out = sku[[
        "产品名",
        "sku",
        "订单数",
        "签收订单数",
        "签收金额",
        "利润",
        "签收率",
        "人民币利润",
        "每单利润",
        "签收毛利率",
    ]].rename(columns={
        "订单数": "订单量",
        "签收毛利率": "毛利润率",
    })
    # 为前端汇总提供统一字段名
    out["毛利率分子"] = out["利润"]  # 印尼盾
    out["毛利率分母"] = out["签收金额"]  # 印尼盾

    # 处理缺失与排序
    for col in ["签收率", "毛利润率", "每单利润", "人民币利润"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.fillna({
        "签收率": 0, "毛利润率": 0, "每单利润": 0, "人民币利润": 0,
        "签收订单数": 0, "签收金额": 0, "利润": 0, "毛利率分子": 0, "毛利率分母": 0
    })
    out = out.sort_values(by="订单量", ascending=False, kind="mergesort").reset_index(drop=True)

    return out

if __name__ == "__main__":
    # 测试用例
    test_order_files = ["1-2月bigseller订单表跑6.xlsx"]
    test_settlement_files = ["跑6结算表结算时间1-3月.xlsx"]
    test_consumption_file = "产品消耗表.xlsx"
    
    # 检查测试文件是否存在
    missing_files = []
    for f in test_order_files + test_settlement_files + [test_consumption_file]:
        if not Path(f).exists():
            missing_files.append(f)
    
    if missing_files:
        print(f"❌ 找不到测试文件: {missing_files}")
        print("请确保测试文件存在或直接通过 Flask 应用使用此模块")
    else:
        process_financial_data(
            order_files=test_order_files,
            settlement_files=test_settlement_files,
            consumption_file=test_consumption_file
        )
