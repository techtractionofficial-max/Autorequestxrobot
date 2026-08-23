from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from database import db
from keyboards import (
    get_main_menu,
    get_store_req_keyboard,
    get_pending_panel_keyboard,
    get_admin_panel_keyboard
)
from config import config

router = Router()

@router.message(CommandStart())
async def start_handler(message: Message):
    await db.register_user(
        user_id=message.from_user.id,
        first_name=message.from_user.first_name,
        username=message.from_user.username
    )
    
    # Custom Inline Buttons for your channels (Not Forced)
    start_buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Join Official Channel 1", url="https://t.me/+zplxZ63hjiI0MzE1")],
        [InlineKeyboardButton(text="📢 Join Official Channel 2", url="https://t.me/cybersecmastery")]
    ])
    
    caption = (
        f"<b>⚡ High-Speed Request Manager</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Welcome, <b>{message.from_user.first_name}</b>!\n\n"
        f"<b>⚙️ Core Capabilities:</b>\n"
        f"• <i>Instant Auto-Approval</i> for Channels\n"
        f"• <i>Promotional DMs</i> to incoming users\n"
        f"• <i>High-Speed Batch Mode</i>: 10,000+ queues\n\n"
        f"<i>Please join our channels below! 👇</i>"
    )
    
    # Send Image with Text and Buttons
    await message.answer_photo(
        photo=config.START_PHOTO_URL,
        caption=caption,
        parse_mode="HTML",
        reply_markup=start_buttons
    )
    
    # Send the Reply Keyboard Menu separately
    await message.answer(
        "<i>Use the menu below to manage your bot settings:</i>",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )

@router.message(F.text == "📩 Store Req")
async def store_req_view(message: Message):
    bot_info = await message.bot.get_me()
    text = (
        "<b>📩 Auto Store Request Accept</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>⚙️ Setup Instructions:</b>\n"
        "1. Add this bot as an <b>Admin</b> to your Channel.\n"
        "2. Ensure the <b>'Add Members'</b> permission is ON.\n\n"
        "<b>⚡ Commands:</b>\n"
        "• <code>/approve 100</code> — Batch-approves 100 pending users."
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_store_req_keyboard(bot_info.username))

@router.message(F.text == "👥 Pending Req")
async def pending_req_view(message: Message):
    bot_info = await message.bot.get_me()
    text = (
        "<b>👥 Pending Request Hub</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Manage your pending approval queues across all connected channels."
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_pending_panel_keyboard(bot_info.username))

@router.message(F.text == "📊 Stats")
async def stats_view(message: Message):
    stats = await db.get_global_stats()
    text = (
        "<b>📊 Global Engine Statistics</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• <b>Active Channels:</b> <code>{stats['total_channels']}</code>\n"
        f"• <b>Indexed Users:</b> <code>{stats['total_users']}</code>\n"
        f"• <b>Pending Requests Queue:</b> <code>{stats['pending_requests']}</code>\n\n"
        "🟢 <b>Status:</b> <i>Online & Running at Maximum Speed</i>"
    )
    await message.answer(text, parse_mode="HTML")

# FIXED: Missing Settings Menu
@router.message(F.text == "⚙️ Settings")
async def settings_view(message: Message):
    bot_info = await message.bot.get_me()
    await message.answer(
        "<b>⚙️ Bot Configuration Menu</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Configure your channel connections below:",
        parse_mode="HTML", 
        reply_markup=get_store_req_keyboard(bot_info.username)
    )

# FIXED: Missing More Menu
@router.message(F.text == "📁 More")
async def more_view(message: Message):
    await message.answer(
        "<b>📁 Additional Options</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "• <b>Admin Panel:</b> Send <code>/admin</code> to broadcast.\n"
        "• <b>Help:</b> Tap the help button in the settings menu.",
        parse_mode="HTML"
    )

@router.message(Command("admin"), F.from_user.id.in_(config.ADMIN_IDS))
async def admin_panel_handler(message: Message):
    await message.answer(
        "<b>🛡️ Master Administration Console</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Select an operation below:",
        parse_mode="HTML",
        reply_markup=get_admin_panel_keyboard()
    )

# FIXED: Broken Callbacks (Back, Auto-Settings, Help)
@router.callback_query(F.data == "btn_home")
async def back_home_callback(call: CallbackQuery):
    await call.message.edit_text("<b>Returned to Main Dashboard.</b>", parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "btn_auto_settings")
async def auto_settings_cb(call: CallbackQuery):
    await call.answer("⚙️ Auto-Approve is currently ENABLED by default for all connected channels.", show_alert=True)

@router.callback_query(F.data == "btn_help")
async def help_cb(call: CallbackQuery):
    help_text = (
        "<b>❓ Help & Commands Guide</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "1. Add bot as admin to your channel.\n"
        "2. Turn on 'Manage Join Requests'.\n"
        "3. Send <code>/approve 100</code> inside the channel to manually accept requests.\n"
        "4. Send <code>/admin</code> here in DMs to broadcast."
    )
    # Replaces the message with the help text but keeps the back button
    await call.message.edit_text(help_text, parse_mode="HTML", reply_markup=call.message.reply_markup)
    
