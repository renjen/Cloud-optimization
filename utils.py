import pandas as pd

def parse_tags(tag_str: str) -> dict:
    d = {}
    if not isinstance(tag_str, str): 
        return d
    for kv in tag_str.split(";"):
        if "=" in kv:
            k, v = kv.split("=", 1)
            d[k.strip()] = v.strip()
    return d

def currency(x):
    try:
        return f"${float(x):,.2f}"
    except:
        return x

def kpis(df: pd.DataFrame):
    total = df["cost_usd"].sum()
    by_rg = df.groupby("resource_group")["cost_usd"].sum().sort_values(ascending=False).head(10)
    by_type = df.groupby("resource_type")["cost_usd"].sum().sort_values(ascending=False).head(10)
    return total, by_rg, by_type
