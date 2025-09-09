import re
from typing import Tuple
import pandas as pd


def parse_sku_multiplier(sku: str) -> Tuple[str, int]:
    """Split SKU into base name and quantity multiplier.

    Examples:
        >>> parse_sku_multiplier("xifashui-2")
        ('xifashui', 2)
        >>> parse_sku_multiplier("xifashui*3")
        ('xifashui', 3)
        >>> parse_sku_multiplier("xifashui")
        ('xifashui', 1)
    """
    if not isinstance(sku, str):
        return str(sku), 1
    sku = sku.strip()
    for pattern in (r"^(.*?)-(\d+)$", r"^(.*?)\*(\d+)$"):
        m = re.match(pattern, sku)
        if m:
            base, mult = m.group(1), int(m.group(2))
            return base, mult
    return sku, 1


def preprocess_combo_sku(df: pd.DataFrame, sku_col: str, qty_col: str) -> pd.DataFrame:
    """Normalize combination SKUs and expand quantities.

    Converts entries like ``xifashui-2`` or ``xifashui*2`` to base ``xifashui``
    while multiplying the quantity column accordingly. Single-unit forms such as
    ``xifashui-1`` or ``xifashui*1`` are also normalized to ``xifashui``.
    """
    df = df.copy()
    combo_count = 0
    for idx, sku in df[sku_col].items():
        if pd.isna(sku):
            continue
        base, multiplier = parse_sku_multiplier(str(sku))
        if base != sku or multiplier != 1:
            original_qty = df.at[idx, qty_col]
            new_qty = original_qty * multiplier
            df.at[idx, sku_col] = base
            df.at[idx, qty_col] = new_qty
            combo_count += 1
            print(
                f"🔄 组合SKU转换: {sku} -> {base}, 数量: {original_qty} -> {new_qty}"
            )
    if combo_count > 0:
        print(f"✅ 完成组合SKU预处理: 转换了 {combo_count} 个组合SKU")
    else:
        print("ℹ️  未发现需要处理的组合SKU")
    return df


def normalize_sku_column(df: pd.DataFrame, sku_col: str) -> pd.DataFrame:
    """Normalize SKU column without adjusting quantity.

    Useful for cost tables where only the SKU naming needs to be unified.
    """
    df = df.copy()
    df[sku_col] = df[sku_col].apply(lambda x: parse_sku_multiplier(str(x))[0])
    return df
