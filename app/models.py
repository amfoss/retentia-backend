from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from .database import Base
from .enums import Grade

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    google_id = Column(String, unique=True, index=True, nullable=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    grade = Column(Enum(Grade), nullable=False)
    institute = Column(String, nullable=False)
    city = Column(String, nullable=False)
    marketing = Column(String, nullable=False)
    
class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    
class Topic(Base):
    __tablename__ = "topics"
    id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, unique=True, nullable=False)
    
class Chapter(Base):
    __tablename__ = "chapters"
    id = Column(Integer, primary_key=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, unique=True, nullable=False)
    
class Concept(Base):
    __tablename__ = "concepts"
    id = Column(Integer, primary_key=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)

class Retention(Base):
    __tablename__ = "user_retention"
    id = Column(Integer, primary_key=True, index=True)
    retention = Column(Integer, nullable=False)
    concept_id = Column(Integer, ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    next_revision_date = Column(DateTime, nullable=False)
    concept = relationship("Concept")