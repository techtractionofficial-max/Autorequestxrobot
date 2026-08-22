import re
from typing import Optional
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_main_menu() -> ReplyKeyboardMarkup:
    """Primary persistent reply navigation."""
    keyboard = [
        [KeyboardButton(text="📩 Store Req"), KeyboardButton(text="👥 Pending Req")],
        [KeyboardButton(text="⚙️ Settings"), KeyboardButton(text="📊 Stats")],
        [KeyboardButton(text="📁 More")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_store_req_keyboard(bot_username: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="➕ Add to Channel",
            url=f"https://t.me/{bot_username}?startchannel=true&admin=invite_users+manage_chat"
        ),
        InlineKeyboardButton(
            text="➕ Add to Group",
            url=f"https://t.me/{bot_username}?startgroup=true&admin=invite_users+manage_chat"
        )
    )
    builder.row(
        InlineKeyboardButton(text="⚙️ Auto-Approve Settings", callback_data="btn_auto_settings")
    )
    builder.row(
        InlineKeyboardButton(text="❓ Help & Commands", callback_data="btn_help"),
        InlineKeyboardButton(text="🔙 Back Home", callback_data="btn_home")
    )
    return builder.as_markup()

def get_pending_panel_keyboard(bot_username: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⚡ Approve All Requests", callback_data="btn_approve_all")
    )
    builder.row(
        InlineKeyboardButton(
            text="➕ Add New Channel",
            url=f"https://t.me/{bot_username}?startchannel=true&admin=invite_users+manage_chat"
        ),
        InlineKeyboardButton(
            text="➕ Add New Group",
            url=f"https://t.me/{bot_username}?startgroup=true&admin=invite_users+manage_chat"
        )
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Back Home", callback_data="btn_home")
    )
    return builder.as_markup()

def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📢 New Rich Broadcast", callback_data="admin_broadcast"),
        InlineKeyboardButton(text="📊 Global Analytics", callback_data="admin_stats")
    )
    builder.row(
        InlineKeyboardButton(text="📁 Export Users (.txt)", callback_data="admin_export_users")
    )
    return builder.as_markup()

def parse_broadcast_buttons(text: str) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """
    Extracts custom inline buttons formatted at the bottom of the message.
    Syntax:
        [ Button 1 | https://link1.com ]
        [ Button 2 | https://link2.com ] [ Button 3 | https://link3.com ]
    """
    pattern = r"(\[.+?\|.+?\][\s\n]*)+"
    match = re.search(pattern, text)
    
    if not match:
        return text, None

    button_block = match.group(0)
    cleaned_text = text.replace(button_block, "").strip()

    builder = InlineKeyboardBuilder()
    lines = button_block.strip().split("\n")
    
    for line in lines:
        row_buttons = re.findall(r"\[([^\|\]]+)\|([^\]]+)\]", line)
        if row_buttons:
            builder.row(*[
                InlineKeyboardButton(text=btn_text.strip(), url=btn_url.strip())
                for btn_text, btn_url in row_buttons
            ])
            
    return cleaned_text, builder.as_markup()
  
