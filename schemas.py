from pydantic import BaseModel
from typing import Optional

class Resource(BaseModel):
    subscription_id: str
    resource_group: str
    resource_type: str
    resource_name: str
    location: str
    meter_category: str
    cost_usd: float
    usage_quantity: float
    unit: str
    tags: str
    avg_cpu: Optional[float] = None
    last_30d_active_hours: Optional[float] = None
    attached: Optional[bool] = None
    provisioned_size_gb: Optional[float] = None
    used_size_gb: Optional[float] = None
    avg_dtu: Optional[float] = None

class Recommendation(BaseModel):
    subscription_id: str
    resource_id: str
    finding: str
    action: str
    est_monthly_saving_usd: float
    rationale: str
    severity: str  # High/Med/Low
