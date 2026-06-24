import datetime
from lifesync.tasks.domain.entities import Task
from lifesync.tasks.domain.value_objects import TaskStatus, ShortDescription, Deadline
from lifesync.shared_kernel.domain.value_objects import ChatId
from lifesync.tasks.domain.services import RolloverService

def test_task_status_transitions():
    now = datetime.datetime.now()
    task = Task(
        id=1,
        description=ShortDescription("Test task"),
        status=TaskStatus.TODO,
        deadline=Deadline(None),
        project_id=1,
        chat_id=ChatId(1),
        created_at=now,
        updated_at=now,
        completed_at=None
    )

    task.mark_in_progress(now)
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.completed_at is None

    task.mark_done(now)
    assert task.status == TaskStatus.DONE
    assert task.completed_at == now.date()

    task.mark_todo(now)
    assert task.status == TaskStatus.TODO
    assert task.completed_at is None

def test_rollover_service():
    today = datetime.date(2026, 1, 2)
    t1 = Task(id=1, description=ShortDescription("Task 1"), status=TaskStatus.TODO, deadline=Deadline(None), project_id=1, chat_id=ChatId(1), created_at=datetime.datetime.now(), updated_at=datetime.datetime.now(), completed_at=None)
    t2 = Task(id=2, description=ShortDescription("Task 2"), status=TaskStatus.TODO, deadline=Deadline(None), project_id=1, chat_id=ChatId(1), created_at=datetime.datetime.now(), updated_at=datetime.datetime.now(), completed_at=None)

    service = RolloverService()
    # Defer task 2 to tomorrow
    service.rollover([t1, t2], today, defer_ids=[2])

    assert t1.deadline.value == today
    assert t2.deadline.value == datetime.date(2026, 1, 3)
