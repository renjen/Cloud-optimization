import os
import pandas as pd

# Placeholder to keep the code structure ready.
# Later, you can implement:
# - Azure AD auth (Client Credentials)
# - Call Cost Management Query API for last 30 days grouped by resourceId
# - Join with Metrics APIs for CPU/DTU when available, or tags

def fetch_azure_costs_last_30d() -> pd.DataFrame:
    # For now, return the sample dataset so the app runs without Azure setup.
    return pd.read_csv("data/sample_costs.csv")
