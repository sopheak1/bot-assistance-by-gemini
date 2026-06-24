from datetime import date, datetime

from sqlalchemy import ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from lifesync.persistence.models.base import UserBase


class ProjectModel(UserBase):
    __tablename__ = "projects"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_id: Mapped[int]
    name: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

class TaskModel(UserBase):
    __tablename__ = "tasks"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_id: Mapped[int]
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    description: Mapped[str]
    status: Mapped[str]
    deadline: Mapped[date | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    completed_at: Mapped[date | None]

class HabitModel(UserBase):
    __tablename__ = "habits"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_id: Mapped[int]
    name: Mapped[str]
    habit_type: Mapped[str]
    numeric_target: Mapped[int | None]
    numeric_unit: Mapped[str | None]
    current_streak: Mapped[int] = mapped_column(default=0)
    longest_streak: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

class HabitCheckInModel(UserBase):
    __tablename__ = "habit_checkins"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    habit_id: Mapped[int] = mapped_column(ForeignKey("habits.id"))
    effective_date: Mapped[date]
    value_bool: Mapped[bool | None]
    value_numeric: Mapped[int | None]
    checked_at: Mapped[datetime] = mapped_column(server_default=func.now())

    __table_args__ = (
        UniqueConstraint('habit_id', 'effective_date', name='uq_habit_date'),
    )
