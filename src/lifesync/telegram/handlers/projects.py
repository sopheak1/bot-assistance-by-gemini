from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from lifesync.persistence.uow import SqlAlchemyUnitOfWork
from lifesync.projects.application.use_cases.create_project import (
    CreateProjectRequest,
    CreateProjectUseCase,
)
from lifesync.projects.application.use_cases.list_projects import ListProjectsUseCase
from lifesync.projects.infrastructure.sqlite_project_repository import SqliteProjectRepository
from lifesync.shared_kernel.domain.clock import SystemClock
from lifesync.telegram.keyboards.menus import get_main_menu

router = Router(name="projects")

class CreateProjectWizard(StatesGroup):
    awaiting_name = State()

@router.callback_query(F.data == "menu:projects")
async def show_projects_menu(callback: types.CallbackQuery, user_session: AsyncSession):
    repo = SqliteProjectRepository(user_session)
    use_case = ListProjectsUseCase(repo)
    
    projects = await use_case.execute(callback.message.chat.id)
    
    text = "📁 **Your Projects**\n\n"
    if not projects:
        text += "No projects found."
    else:
        for p in projects:
            text += f"- {p.name} (ID: {p.id})\n"
            
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ New Project", callback_data="project:create")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="menu:main")]
    ])
    
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "menu:main")
async def back_to_main(callback: types.CallbackQuery, domain_context: str):
    await callback.message.edit_text("Main Menu:", reply_markup=get_main_menu(domain_context))
    await callback.answer()

@router.callback_query(F.data == "project:create")
async def start_create_project(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("What is the name of the new project?")
    await state.set_state(CreateProjectWizard.awaiting_name)
    await callback.answer()

@router.message(CreateProjectWizard.awaiting_name)
async def process_project_name(message: types.Message, state: FSMContext, user_session: AsyncSession, domain_context: str):
    
    repo = SqliteProjectRepository(user_session)
    uow = SqlAlchemyUnitOfWork(user_session)
    clock = SystemClock()
    
    use_case = CreateProjectUseCase(repo, uow, clock)
    
    req = CreateProjectRequest(
        chat_id=message.chat.id,
        name=message.text or "Untitled"
    )
    
    try:
        project_id = await use_case.execute(req)
        await message.answer("✅ Project successfully created!", reply_markup=get_main_menu(domain_context))
    except Exception as e:
        await message.answer(f"❌ Error: {e}")
        
    await state.clear()
