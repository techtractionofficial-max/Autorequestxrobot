from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
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
    
    welcome_text = (
        f"<b>⚡ High-Speed Request Manager</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Welcome, <b>{message.from_user.first_name}</b>!\n\n"
        f"<b>⚙️ Core Capabilities:</b>\n"
        f"• <i>Instant Auto-Approval</i> for Channels & Groups\n"
        f"• <i>Promotional DMs</i> sent to incoming users\n"
        f"• <i>High-Speed Batch Mode</i>: Process 10,000+ queues\n\n"
        f"<i>Use the menu below to configure your channels.</i>"
    )
    await message.answer(welcome_text, parse_mode="HTML", reply_markup=get_main_menu())

@router.message(F.text == "📩 Store Req")
async def store_req_view(message: Message):
    bot_info = await message.bot.get_me()
    text = (
        "<b>📩 Auto Store Request Accept</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>⚙️ Setup Instructions:</b>\n"
        "1. Add this bot as an <b>Admin</b> to your Channel or Group.\n"
        "2. Ensure the <b>'Add Members / Manage Requests'</b> permission is ON.\n\n"
        "<b>⚡ Commands:</b>\n"
        "• <code>/approve 100</code> — Batch-approves 100 pending join requests.\n"
        "• <code>/acceptall</code> — Flushes and approves the entire queue."
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_store_req_keyboard(bot_info.username))

@router.message(F.text == "👥 Pending Req")
async def pending_req_view(message: Message):
    bot_info = await message.bot.get_me()
    text = (
        "<b>👥 Pending Request Hub</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Manage your pending approval queues across all configured channels.\n\n"
        "<b>⚠️ Note:</b> Ensure the bot maintains <i>'Add Admins'</i> or <i>'Invite Users'</i> permissions."
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
        f"• <b>Active Delivery Nodes:</b> <code>{stats['active_users']}</code>\n"
        f"• <b>Pending Requests Queue:</b> <code>{stats['pending_requests']}</code>\n"
        f"• <b>Max Engine Throughput:</b> <code>250 approvals/sec</code>\n\n"
        "🟢 <b>Status:</b> <i>Online & Running at Maximum Speed</i>"
    )
    await message.answer(text, parse_mode="HTML")

@router.message(Command("admin"), F.from_user.id.in_(config.ADMIN_IDS))
async def admin_panel_handler(message: Message):
    await message.answer(
        "<b>🛡️ Master Administration Console</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Select an operation below:",
        parse_mode="HTML",
        reply_markup=get_admin_panel_keyboard()
    )

@router.callback_query(F.data == "btn_home")
async def back_home_callback(call: CallbackQuery):
    await call.message.edit_text(
        "<b>Returned to Main Dashboard.</b>",
        parse_mode="HTML"
    )
    await call.answer()
  
