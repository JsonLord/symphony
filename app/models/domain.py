from sqlalchemy import Column, String, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class Project(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String)
    description = Column(String)
    profile_id = Column(String)
    status = Column(String, default="analyzing")
    plandex_plan_id = Column(String, nullable=True)
    tasks = relationship("Task", back_populates="project")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"))
    repository_id = Column(String)
    tag = Column(String)
    status = Column(String, default="pending")
    jules_session_id = Column(String, nullable=True)
    task_type = Column(String, default="standard")
    context = Column(JSON, nullable=True)
    queue_position = Column(Integer, default=0)

    project = relationship("Project", back_populates="tasks")

class SettingsProfile(Base):
    __tablename__ = "settings_profiles"
    id = Column(String, primary_key=True, default=generate_uuid)
    profile_name = Column(String)
    hf_space_id = Column(String, nullable=True)
    parameters = Column(JSON)
