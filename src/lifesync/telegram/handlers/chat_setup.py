from aiogram import F, Router, types
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from lifesync.chat_context.application.use_cases.bind_chat_context import (
    BindChatContextRequest,
    BindChatContextUseCase,
)
from lifesync.chat_context.infrastructure.sqlite_chat_binding_repository import (
    SqliteChatBindingRepository,
)
from lifesync.persistence.uow import SqlAlchemyUnitOfWork
from lifesync.shared_kernel.domain.clock import SystemClock
from lifesync.telegram.keyboards.menus import get_main_menu
from lifesync.users.application.use_cases.register_user import (
    RegisterUserRequest,
    RegisterUserUseCase,
)
from lifesync.users.infrastructure.sqlite_user_settings_repository import (
    SqliteUserSettingsRepository,
)

router = Router(name="chat_setup")

@router.message(Command("start"))
async def cmd_start(message: types.Message, domain_context: str | None = None):
    if not domain_context:
        await message.answer(
            "Welcome to Life-Sync Assistant! 🚀\n\n"
            "To get started, you need to set up this chat as a specific workspace.\n"
            "Use /init_work for Task and Project Management, or /init_habit for Habit Tracking."
        )
    else:
        domain_name = domain_context.lower()
        await message.answer(
            f"Welcome back! This chat is currently your dedicated {domain_name.capitalize()} Workspace.\n\n"
            "Use the menu below to interact with your data.",
            reply_markup=get_main_menu(domain_context)
        )

@router.message(Command("init_work"))
async def cmd_init_work(message: types.Message, bot_session: AsyncSession):
    await _init_domain(message, bot_session, "WORK")

@router.message(Command("init_habit"))
async def cmd_init_habit(message: types.Message, bot_session: AsyncSession):
    await _init_domain(message, bot_session, "HABIT")

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "📚 **Life-Sync Assistant Commands**\n\n"
        "/start - Show the main menu (requires a workspace)\n"
        "/init_work - Set up this chat as your Work Workspace\n"
        "/init_habit - Set up this chat as your Habit Workspace\n"
        "/help - Show this help message\n\n"
        "Most interactions are done via the inline buttons by sending `/start` after initializing.",
        parse_mode="Markdown"
    )

async def _init_domain(message: types.Message, bot_session: AsyncSession, domain: str):
    if not message.from_user:
        return
        
    chat_repo = SqliteChatBindingRepository(bot_session)
    user_repo = SqliteUserSettingsRepository(bot_session)
    uow = SqlAlchemyUnitOfWork(bot_session)
    clock = SystemClock()
    
    bind_use_case = BindChatContextUseCase(chat_repo, uow, clock)
    register_use_case = RegisterUserUseCase(user_repo, uow, clock)
    
    await bind_use_case.execute(BindChatContextRequest(
        chat_id=message.chat.id,
        telegram_id=message.from_user.id,
        domain_context=domain
    ))
    
    await register_use_case.execute(RegisterUserRequest(telegram_id=message.from_user.id))
    
    await message.answer(
        f"✅ This chat is now your dedicated {domain} Workspace.\nYour default settings (UTC+7 Timezone, 9 AM Morning Plan, 2 AM Daily Reset) have been applied.\n\n"
        "Use the menu below to get started:",
        reply_markup=get_main_menu(domain)
    )

from aiogram.filters import StateFilter

@router.message(F.text, StateFilter(None))
async def fallback_text_handler(message: types.Message, domain_context: str | None = None):
    if domain_context:
        await message.answer("I'm not sure what you mean. Please use the menu buttons to interact!", reply_markup=get_main_menu(domain_context))
    else:
        await message.answer("Please set up this chat first using /init_work or /init_habit.")
