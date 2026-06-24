from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu(domain_context: str) -> InlineKeyboardMarkup:
    if domain_context == "WORK":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📁 Projects", callback_data="menu:projects")],
            [InlineKeyboardButton(text="📝 Tasks", callback_data="menu:tasks")],
            [InlineKeyboardButton(text="📊 Report", callback_data="menu:report")],
            [InlineKeyboardButton(text="⚙️ Settings", callback_data="menu:settings")],
        ])
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔥 Habits", callback_data="menu:habits")],
            [InlineKeyboardButton(text="✅ Check-in", callback_data="menu:checkin")],
            [InlineKeyboardButton(text="📊 Report", callback_data="menu:habit_report")],
            [InlineKeyboardButton(text="⚙️ Settings", callback_data="menu:settings")],
        ])
