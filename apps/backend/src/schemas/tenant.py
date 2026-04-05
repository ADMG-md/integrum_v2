from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class TenantBase(BaseModel):
    name: str = Field(..., example="EPS sanitas")
    slug: str = Field(..., example="eps-sanitas")
    subscription_plan: str = "standard"

class TenantCreate(TenantBase):
    pass

class TenantRead(TenantBase):
    id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
