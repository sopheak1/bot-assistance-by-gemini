from aiogram import Router, types
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
            "To get started, you need to bind this chat to a specific domain.\n"
            "Use /init_work for task and project management, or /init_habit for habit tracking."
        )
    else:
        await message.answer(
            f"Welcome back! This chat is currently bound to the {domain_context} domain.\n\n"
            "Use the menu to interact with your data.",
            reply_markup=get_main_menu(domain_context)
        )

@router.message(Command("init_work"))
async def cmd_init_work(message: types.Message, bot_session: AsyncSession):
    await _init_domain(message, bot_session, "WORK")

@router.message(Command("init_habit"))
async def cmd_init_habit(message: types.Message, bot_session: AsyncSession):
    await _init_domain(message, bot_session, "HABIT")

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
    
    await message.answer(f"✅ This chat is now bound to the {domain} domain.\nYour default settings (UTC+7 timezone, 9 AM standup, 2 AM rollover) have been applied.")
