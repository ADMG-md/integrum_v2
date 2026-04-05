from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import Base
import uuid
from datetime import datetime
from typing import List

class Tenant(Base):
    """
    Mission 12: Multi-Tenancy Governance.
    Represents an Enterprise Client (EPS, Clinic, Hospital).
    """
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False) # e.g. 'eps-sanitas'
    
    # Configuration / Governance
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    subscription_plan: Mapped[str] = mapped_column(String(50), default="standard") # standard, premium, clinical_research
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    # In a real SaMD, patients and users would have hard FKs to this. 
    # For now we keep the string tenant_id for flexibility but this model manages the registry.
