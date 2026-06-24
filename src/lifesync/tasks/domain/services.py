from datetime import date
import datetime
from lifesync.tasks.domain.entities import Task
from lifesync.tasks.domain.value_objects import Deadline

class RolloverService:
    def rollover(self, tasks: list[Task], today: date, defer_ids: list[int], defer_date: date | None = None) -> None:
        """
        Modifies tasks in place.
        Tasks whose ID is in defer_ids are deferred to defer_date (default: tomorrow).
        Other tasks are moved to today.
        """
        if defer_date is None:
            defer_date = today + datetime.timedelta(days=1)
            
        for task in tasks:
            if task.id in defer_ids:
                task.deadline = Deadline(defer_date)
            else:
                task.deadline = Deadline(today)
