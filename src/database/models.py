"""Модели данных для базы данных."""
from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime, ForeignKey, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum

Base = declarative_base()

class ProcessStatus(enum.Enum):
    """Статусы обработки"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Brand(Base):
    """Модель для брендов"""
    __tablename__ = 'brands'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    url = Column(String(500), nullable=False)
    category = Column(String(255))
    data = Column(JSON)  # Все данные бренда в JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    products = relationship("Product", back_populates="brand")
    progress = relationship("PipelineProgress", back_populates="brand")

class Product(Base):
    """Модель для продуктов"""
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    product_id = Column(String(255), unique=True, nullable=False)
    brand_id = Column(Integer, ForeignKey('brands.id'))
    name = Column(String(255))
    url = Column(String(500))
    description = Column(Text)
    data = Column(JSON)  # Все данные продукта в JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    brand = relationship("Brand", back_populates="products")

class PipelineProgress(Base):
    """Модель для отслеживания прогресса пайплайна"""
    __tablename__ = 'pipeline_progress'

    id = Column(Integer, primary_key=True)
    brand_id = Column(Integer, ForeignKey('brands.id'))
    status = Column(Enum(ProcessStatus), default=ProcessStatus.PENDING)
    error = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    brand = relationship("Brand", back_populates="progress") 