from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from lifesync.habits.application.use_cases.check_in_habit import (
    CheckInHabitRequest,
    CheckInHabitUseCase,
)
from lifesync.habits.application.use_cases.create_habit import (
    CreateHabitRequest,
    CreateHabitUseCase,
)
from lifesync.habits.application.use_cases.list_habits_for_standup import (
    ListHabitsForStandupUseCase,
)
from lifesync.habits.domain.services import StreakCalculationService
from lifesync.habits.infrastructure.sqlite_habit_repository import (
    SqliteHabitCheckInRepository,
    SqliteHabitRepository,
)
from lifesync.persistence.uow import SqlAlchemyUnitOfWork
from lifesync.shared_kernel.domain.clock import SystemClock
from lifesync.telegram.keyboards.menus import get_main_menu

router = Router(name="habits")


class CreateHabitWizard(StatesGroup):
    awaiting_name = State()


@router.callback_query(F.data == "menu:habits")
async def show_habits_menu(callback: types.CallbackQuery, user_session: AsyncSession) -> None:
    if not isinstance(callback.message, types.Message):
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ New Habit", callback_data="habit:create")],
            [InlineKeyboardButton(text="🔙 Back", callback_data="menu:main")],
        ]
    )

    await callback.message.edit_text("🔥 **Habits Menu**", reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "habit:create")
async def start_create_habit(callback: types.CallbackQuery, state: FSMContext) -> None:
    if not isinstance(callback.message, types.Message):
        return
    await callback.message.answer("What is the name of the new habit?")
    await state.set_state(CreateHabitWizard.awaiting_name)
    await callback.answer()


@router.message(CreateHabitWizard.awaiting_name)
async def process_habit_name(
    message: types.Message, state: FSMContext, user_session: AsyncSession, domain_context: str
) -> None:
    repo = SqliteHabitRepository(user_session)
    uow = SqlAlchemyUnitOfWork(user_session)
    clock = SystemClock()

    use_case = CreateHabitUseCase(repo, uow, clock)

    req = CreateHabitRequest(
        chat_id=message.chat.id, name=message.text or "Untitled", habit_type="BINARY"
    )

    try:
        await use_case.execute(req)
        await message.answer(
            "✅ Habit successfully added!", reply_markup=get_main_menu(domain_context)
        )
    except Exception as e:
        await message.answer(f"❌ Error: {e}")

    await state.clear()


@router.callback_query(F.data == "menu:checkin")
async def show_checkin_menu(callback: types.CallbackQuery, user_session: AsyncSession) -> None:
    if not isinstance(callback.message, types.Message):
        return
    repo = SqliteHabitRepository(user_session)
    checkin_repo = SqliteHabitCheckInRepository(user_session)
    use_case = ListHabitsForStandupUseCase(repo, checkin_repo)
    clock = SystemClock()

    habits = await use_case.execute(callback.message.chat.id, clock.now().date())

    buttons = []
    for h in habits:
        status = "✅" if h.checked_in_today else "❌"
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{status} {h.name}", callback_data=f"habit:checkin:{h.habit_id}"
                )
            ]
        )
    buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="menu:main")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text("Check-in for today:", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("habit:checkin:"))
async def process_habit_checkin(
    callback: types.CallbackQuery, user_session: AsyncSession, domain_context: str
) -> None:
    if not isinstance(callback.message, types.Message) or not callback.data:
        return
    habit_id = int(callback.data.split(":")[2])

    repo = SqliteHabitRepository(user_session)
    checkin_repo = SqliteHabitCheckInRepository(user_session)
    uow = SqlAlchemyUnitOfWork(user_session)
    clock = SystemClock()
    streak_svc = StreakCalculationService()

    use_case = CheckInHabitUseCase(repo, checkin_repo, streak_svc, uow, clock)

    req = CheckInHabitRequest(habit_id=habit_id, effective_date=clock.now().date(), value_bool=True)

    try:
        await use_case.execute(req)
        await callback.message.answer("✅ Checked in!", reply_markup=get_main_menu(domain_context))
    except Exception as e:
        await callback.message.answer(f"❌ Error: {e}")

    await callback.answer()
