from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)  
    # New fields
    profile_photo = Column(String, nullable=True) # URL or path
    about = Column(Text, nullable=True)
    linkedin_url = Column(String, nullable=True)
    github_url = Column(String, nullable=True)
    twitter_url = Column(String, nullable=True)
    # Relationships
    skills_offered = relationship("UserSkill", back_populates="user", cascade="all, delete-orphan")
    skills_needed = relationship("SkillRequest", back_populates="user", cascade="all, delete-orphan")

class UserSkill(Base):
    __tablename__ = "user_skills"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    skill_name = Column(String, index=True)
    skill_level = Column(String)  # beginner, intermediate, expert
    category_id = Column(Integer, ForeignKey("categories.id"))
    
    user = relationship("User", back_populates="skills_offered")
    category = relationship("Category")

class SkillRequest(Base):
    __tablename__ = "skill_requests" 
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    skill_name = Column(String, index=True)
    description = Column(Text)  # What they want to learn
    
    user = relationship("User", back_populates="skills_needed")


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    is_read = Column(Integer, default=0)  # 0 = unread, 1 = read
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])

class VideoSession(Base):
    __tablename__ = "video_sessions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    room_id = Column(String, unique=True, index=True)
    user1_email = Column(String, index=True)
    user2_email = Column(String, index=True)
    meeting_url = Column(String)
    status = Column(String, default="created")  # created, active, ended
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)



class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    author_email = Column(String)
    content = Column(Text)
    category = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow) # <--- CRUCIAL

class GroupChat(Base):
    __tablename__ = "group_chats"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)

class GroupMessage(Base):
    __tablename__ = "group_messages"
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("group_chats.id"))
    sender_email = Column(String)
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    learner_email = Column(String)
    teacher_email = Column(String)
    skill_name = Column(String)
    session_date = Column(String)  # Format: YYYY-MM-DD
    session_time = Column(String)  # Format: HH:MM
    status = Column(String, default="pending") # pending, accepted, declined
    created_at = Column(DateTime, default=datetime.utcnow)