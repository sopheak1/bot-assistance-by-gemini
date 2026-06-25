import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from lifesync.persistence.uow import SqlAlchemyUnitOfWork
from lifesync.projects.application.use_cases.list_projects import ListProjectsUseCase
from lifesync.projects.infrastructure.sqlite_project_repository import SqliteProjectRepository
from lifesync.shared_kernel.domain.clock import SystemClock
from lifesync.tasks.application.use_cases.create_task import CreateTaskRequest, CreateTaskUseCase
from lifesync.tasks.infrastructure.sqlite_task_repository import SqliteTaskRepository
from lifesync.telegram.keyboards.menus import get_main_menu

logger = logging.getLogger(__name__)

router = Router(name="tasks")

class CreateTaskWizard(StatesGroup):
    awaiting_project = State()
    awaiting_description = State()

@router.callback_query(F.data == "menu:tasks")
async def show_tasks_menu(callback: types.CallbackQuery, user_session: AsyncSession) -> None:
    if not isinstance(callback.message, types.Message):
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ New Task", callback_data="task:create")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="menu:main")]
    ])
    
    await callback.message.edit_text("📝 **Tasks Menu**", reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "task:create")
async def start_create_task(callback: types.CallbackQuery, state: FSMContext, user_session: AsyncSession) -> None:
    if not isinstance(callback.message, types.Message):
        return
    repo = SqliteProjectRepository(user_session)
    projects = await ListProjectsUseCase(repo).execute(callback.message.chat.id)
    
    if not projects:
        await callback.message.answer("You need to create a Project first before adding a task.")
        await callback.answer()
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=p.name, callback_data=f"task:project:{p.id}")] for p in projects
    ])
    
    await callback.message.answer("Select a project for the new task:", reply_markup=kb)
    await state.set_state(CreateTaskWizard.awaiting_project)
    await callback.answer()

@router.callback_query(CreateTaskWizard.awaiting_project, F.data.startswith("task:project:"))
async def process_task_project(callback: types.CallbackQuery, state: FSMContext) -> None:
    if not isinstance(callback.message, types.Message) or not callback.data:
        return
    project_id = int(callback.data.split(":")[2])
    await state.update_data(project_id=project_id)
    
    await callback.message.answer("What is the task description?")
    await state.set_state(CreateTaskWizard.awaiting_description)
    await callback.answer()

@router.message(CreateTaskWizard.awaiting_description)
async def process_task_description(message: types.Message, state: FSMContext, user_session: AsyncSession, domain_context: str) -> None:
    data = await state.get_data()
    project_id = data["project_id"]
    
    repo = SqliteTaskRepository(user_session)
    uow = SqlAlchemyUnitOfWork(user_session)
    clock = SystemClock()
    
    use_case = CreateTaskUseCase(repo, uow, clock)
    
    req = CreateTaskRequest(
        chat_id=message.chat.id,
        project_id=project_id,
        description=message.text or "Untitled",
        deadline=None
    )
    
    try:
        task_id = await use_case.execute(req)
        await message.answer("✅ Task successfully added!", reply_markup=get_main_menu(domain_context))
    except Exception as e:
        await message.answer(f"❌ Error: {e}")
        
    await state.clear()
