import pandas as pd
import numpy as np
from typing import List
from .schemas import Recommendation

def _fmt_id(row):
    return f"{row['subscription_id']}/{row['resource_group']}/{row['resource_type']}/{row['resource_name']}"

def detect_unused_vms(df: pd.DataFrame) -> List[Recommendation]:
    c = df[
        (df["resource_type"].str.contains("Microsoft.Compute/virtualMachines", case=False, na=False)) &
        (
            (df["last_30d_active_hours"].fillna(0) < 24) |
            (df["avg_cpu"].fillna(0) < 5)
        )
    ]
    recs = []
    for _, r in c.iterrows():
        save = round(float(r["cost_usd"]) * 0.8, 2)  # assume deallocate saves ~80%
        rationale = f"avg_cpu={r.get('avg_cpu', np.nan)}%, active_hours={r.get('last_30d_active_hours', np.nan)} in last 30d."
        recs.append(Recommendation(
            subscription_id=r["subscription_id"],
            resource_id=_fmt_id(r),
            finding="Likely idle VM",
            action="Stop/deallocate or schedule off-hours; consider Azure Automation.",
            est_monthly_saving_usd=save,
            rationale=rationale,
            severity="High" if r["cost_usd"] >= 150 else "Medium"
        ))
    return recs

def detect_unattached_disks(df: pd.DataFrame) -> List[Recommendation]:
    c = df[
        (df["resource_type"].str.contains("disks", case=False, na=False)) &
        (df["attached"].astype(str).str.lower().isin(["false", "0", "no", "nan"]))
    ]
    recs = []
    for _, r in c.iterrows():
        save = round(float(r["cost_usd"]), 2)  # delete saves current disk cost
        recs.append(Recommendation(
            subscription_id=r["subscription_id"],
            resource_id=_fmt_id(r),
            finding="Unattached managed disk",
            action="Delete or move to cheaper snapshot tier.",
            est_monthly_saving_usd=save,
            rationale="Disk shows attached=false.",
            severity="High" if save > 20 else "Medium"
        ))
    return recs

def detect_storage_tiering(df: pd.DataFrame) -> List[Recommendation]:
    c = df[df["resource_type"].str.contains("Microsoft.Storage/storageAccounts", case=False, na=False)]
    recs = []
    for _, r in c.iterrows():
        if (r.get("used_size_gb", 0) / max(r.get("provisioned_size_gb", 1), 1)) < 0.2:
            save = round(float(r["cost_usd"]) * 0.3, 2)  # assume 30% by moving to Cool/Archive
            rationale = f"Utilization {r.get('used_size_gb',0)}/{r.get('provisioned_size_gb',1)} GB (~{(r.get('used_size_gb',0)/max(r.get('provisioned_size_gb',1),1))*100:.1f}%)."
            recs.append(Recommendation(
                subscription_id=r["subscription_id"],
                resource_id=_fmt_id(r),
                finding="Low-utilized storage account",
                action="Move rarely-accessed data to Cool/Archive tier; enable lifecycle rules.",
                est_monthly_saving_usd=save,
                rationale=rationale,
                severity="Medium"
            ))
    return recs

def detect_rightsize_sql(df: pd.DataFrame) -> List[Recommendation]:
    c = df[df["resource_type"].str.contains("Microsoft.Sql/servers/databases", case=False, na=False)]
    c = c[c["avg_dtu"].fillna(100) < 20]
    recs = []
    for _, r in c.iterrows():
        save = round(float(r["cost_usd"]) * 0.4, 2)  # assume 40% by down-tiering
        recs.append(Recommendation(
            subscription_id=r["subscription_id"],
            resource_id=_fmt_id(r),
            finding="Underutilized SQL Database",
            action="Downsize service tier or switch to serverless.",
            est_monthly_saving_usd=save,
            rationale=f"avg_dtu={r.get('avg_dtu', np.nan)}.",
            severity="High" if r["cost_usd"] >= 300 else "Medium"
        ))
    return recs

def detect_savings_plan_opportunity(df: pd.DataFrame) -> List[Recommendation]:
    vms = df[df["resource_type"].str.contains("Microsoft.Compute/virtualMachines", case=False, na=False)]
    vms = vms[vms["last_30d_active_hours"].fillna(0) >= 400]  # fairly steady usage
    recs = []
    for _, r in vms.iterrows():
        save = round(float(r["cost_usd"]) * 0.25, 2)  # rough Savings Plan benefit
        recs.append(Recommendation(
            subscription_id=r["subscription_id"],
            resource_id=_fmt_id(r),
            finding="Savings Plan/RI candidate",
            action="Evaluate 1-yr Compute Savings Plan (or RI) for this steady VM.",
            est_monthly_saving_usd=save,
            rationale=f"Consistent {r['last_30d_active_hours']}h last 30d; cost ${r['cost_usd']:.2f}.",
            severity="Medium"
        ))
    return recs

def generate_recommendations(df: pd.DataFrame) -> pd.DataFrame:
    rules = [
        detect_unused_vms,
        detect_unattached_disks,
        detect_storage_tiering,
        detect_rightsize_sql,
        detect_savings_plan_opportunity,
    ]
    all_recs = []
    for rule in rules:
        all_recs.extend(rule(df.copy()))
    if not all_recs:
        return pd.DataFrame(columns=["subscription_id","resource_id","finding","action","est_monthly_saving_usd","rationale","severity"])
    out = pd.DataFrame([r.model_dump() for r in all_recs]).sort_values("est_monthly_saving_usd", ascending=False)
    out["id"] = range(1, len(out)+1)
    out = out[["id","severity","subscription_id","resource_id","finding","action","est_monthly_saving_usd","rationale"]]
    return out
