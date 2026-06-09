from __future__ import annotations  

import uuid  
from datetime import datetime, UTC  
from sqlalchemy import String, ForeignKey, DateTime  
from sqlalchemy.orm import Mapped, mapped_column, relationship  
from sqlalchemy.dialects.postgresql import UUID  
from app.core.database import Base 
  

class User(Base):  
    __tablename__ = "users"  

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)  
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)  
    role: Mapped[str] = mapped_column(String, nullable=False, default="viewer")  
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)  
    token_version: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))  

    organization = relationship("Organization", back_populates="users") 
