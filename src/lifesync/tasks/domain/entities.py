from dataclasses import dataclass
from datetime import date, datetime

from lifesync.shared_kernel.domain.value_objects import ChatId
from lifesync.tasks.domain.value_objects import Deadline, ShortDescription, TaskStatus


@dataclass
class Task:
    id: int | None
    description: ShortDescription
    status: TaskStatus
    deadline: Deadline
    project_id: int
    chat_id: ChatId
    created_at: datetime
    updated_at: datetime
    completed_at: date | None

    def mark_done(self, clock_now: datetime) -> None:
        self.status = TaskStatus.DONE
        self.completed_at = clock_now.date()
        self.updated_at = clock_now

    def mark_in_progress(self, clock_now: datetime) -> None:
        self.status = TaskStatus.IN_PROGRESS
        self.completed_at = None
        self.updated_at = clock_now

    def mark_todo(self, clock_now: datetime) -> None:
        self.status = TaskStatus.TODO
        self.completed_at = None
        self.updated_at = clock_now

    def reschedule(self, new_deadline: Deadline, clock_now: datetime) -> None:
        self.deadline = new_deadline
        self.updated_at = clock_now

    def defer_to(self, new_date: date, clock_now: datetime) -> None:
        self.deadline = Deadline(new_date)
        self.updated_at = clock_now
