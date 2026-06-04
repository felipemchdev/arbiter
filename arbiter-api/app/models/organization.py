from __future__ import annotations  
  
import uuid  
from datetime import UTC, datetime  
  
from sqlalchemy import DateTime, String  
from sqlalchemy.orm import Mapped, mapped_column, relationship  
  
from app.core.database import Base  
  
  
class Organization(Base):  
    __tablename__ = "organizations"  
  
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)  
    name: Mapped[str] = mapped_column(String(255), nullable=False)  
    api_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)  
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)  
  
    pipelines: Mapped[list["Pipeline"]] = relationship(back_populates="organization", cascade="all, delete-orphan")  
    users = relationship("User", back_populates="organization") 
