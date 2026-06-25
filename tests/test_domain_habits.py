import datetime

from lifesync.habits.domain.entities import Habit, HabitCheckIn
from lifesync.habits.domain.services import StreakCalculationService
from lifesync.habits.domain.value_objects import HabitType, Streak
from lifesync.shared_kernel.domain.value_objects import ChatId


def test_streak_calculation_increment() -> None:
    habit = Habit(
        id=1,
        name="Read",
        habit_type=HabitType.BINARY,
        numeric_target=None,
        numeric_unit=None,
        streak=Streak(5, 10),
        chat_id=ChatId(1),
        created_at=datetime.datetime.now(),
    )
    last_checkin = HabitCheckIn(
        id=1,
        habit_id=1,
        effective_date=datetime.date(2026, 1, 1),
        value_bool=True,
        value_numeric=None,
        checked_at=datetime.datetime.now(),
    )

    service = StreakCalculationService()
    # Check in on the next day
    new_streak = service.compute_streak(habit, last_checkin, datetime.date(2026, 1, 2))
    assert new_streak.current == 6
    assert new_streak.longest == 10


def test_streak_calculation_reset() -> None:
    habit = Habit(
        id=1,
        name="Read",
        habit_type=HabitType.BINARY,
        numeric_target=None,
        numeric_unit=None,
        streak=Streak(5, 10),
        chat_id=ChatId(1),
        created_at=datetime.datetime.now(),
    )
    last_checkin = HabitCheckIn(
        id=1,
        habit_id=1,
        effective_date=datetime.date(2026, 1, 1),
        value_bool=True,
        value_numeric=None,
        checked_at=datetime.datetime.now(),
    )

    service = StreakCalculationService()
    # Missed a day
    new_streak = service.compute_streak(habit, last_checkin, datetime.date(2026, 1, 3))
    assert new_streak.current == 1
    assert new_streak.longest == 10


def test_streak_calculation_same_day() -> None:
    habit = Habit(
        id=1,
        name="Read",
        habit_type=HabitType.BINARY,
        numeric_target=None,
        numeric_unit=None,
        streak=Streak(5, 10),
        chat_id=ChatId(1),
        created_at=datetime.datetime.now(),
    )
    last_checkin = HabitCheckIn(
        id=1,
        habit_id=1,
        effective_date=datetime.date(2026, 1, 1),
        value_bool=True,
        value_numeric=None,
        checked_at=datetime.datetime.now(),
    )

    service = StreakCalculationService()
    # Check in on the same day (should be idempotent for the streak)
    new_streak = service.compute_streak(habit, last_checkin, datetime.date(2026, 1, 1))
    assert new_streak.current == 5
    assert new_streak.longest == 10


def test_streak_longest_update() -> None:
    habit = Habit(
        id=1,
        name="Read",
        habit_type=HabitType.BINARY,
        numeric_target=None,
        numeric_unit=None,
        streak=Streak(10, 10),
        chat_id=ChatId(1),
        created_at=datetime.datetime.now(),
    )
    last_checkin = HabitCheckIn(
        id=1,
        habit_id=1,
        effective_date=datetime.date(2026, 1, 1),
        value_bool=True,
        value_numeric=None,
        checked_at=datetime.datetime.now(),
    )

    service = StreakCalculationService()
    # Check in on next day, current reaches 11, longest should become 11
    new_streak = service.compute_streak(habit, last_checkin, datetime.date(2026, 1, 2))
    assert new_streak.current == 11
    assert new_streak.longest == 11
