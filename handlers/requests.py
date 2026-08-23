import asyncio
from aiogram import Router, F
from aiogram.types import ChatJoinRequest, Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError
from database import db
from config import config

router = Router()

@router.chat_join_request()
async def join_request_handler(event: ChatJoinRequest):
    user = event.from_user
    chat = event.chat

    # 1. Register user in database
    await db.register_user(
        user_id=user.id,
        first_name=user.first_name,
        username=user.username
    )

    # 2. Retrieve channel settings
    channel_data = await db.get_channel(chat.id)
    if not channel_data:
        await db.add_channel(channel_id=chat.id, owner_id=user.id, title=chat.title)
        auto_approve = 1
    else:
        _, _, _, auto_approve, _, _, _ = channel_data

    # CUSTOMIZE GREETING TEXT HERE
    custom_dm = (
        f"<b>Hello {user.first_name}!</b> 🎉\n\n"
        "Your request has been approved. Welcome to our official community!\n\n"
        "<i>Tap the button below to get your VIP link:</i>"
    )

    try:
        # We send a callback button. When they click this, they get locked in for broadcasts!
        promo_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎁 Tap to Reveal VIP Link", callback_data=f"vip_{chat.id}")]
        ])
        
        await event.bot.send_photo(
            chat_id=user.id,
            photo=config.WELCOME_PHOTO_URL,
            caption=custom_dm,
            parse_mode="HTML",
            reply_markup=promo_keyboard
        )
    except (TelegramForbiddenError, Exception):
        pass  

    # 4. Handle Approval
    if auto_approve:
        try:
            await event.approve()
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            await event.approve()
        except Exception:
            pass
    else:
        await db.add_pending_request(channel_id=chat.id, user_id=user.id)


# ==========================================
# ⚡ THE MAGIC REVEAL AND DELETE FUNCTION
# ==========================================
@router.callback_query(F.data.startswith("vip_"))
async def reveal_vip_link(call: CallbackQuery):
    # 1. Instantly delete the massive greeting photo
    try:
        await call.message.delete()
    except Exception:
        pass
    
    # 2. Fetch the correct VIP link for this specific channel
    channel_id = int(call.data.split("_")[1])
    channel_data = await db.get_channel(channel_id)
    
    btn_text = "🔥 Join VIP Channel"
    btn_url = "https://t.me/Telegram" # Default fallback
    
    if channel_data:
        _, _, _, _, _, db_btn_text, db_btn_url = channel_data
        if db_btn_text and db_btn_url:
            btn_text = db_btn_text
            btn_url = db_btn_url

    # 3. Give them the actual URL link in a small, clean message
    final_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn_text, url=btn_url)]
    ])
    
    await call.message.answer(
        "<b>✅ Access Granted!</b>\n\nClick below to join:",
        parse_mode="HTML",
        reply_markup=final_keyboard
    )
    await call.answer()


# ==========================================
# MANUAL APPROVAL COMMANDS
# ==========================================
@router.callback_query(F.data == "btn_approve_all")
async def approve_all_cb(call: CallbackQuery):
    await call.answer(
        "⚡ High-Speed Mode:\nTo approve requests, go to your specific Telegram Channel/Group and type:\n\n/approve 100", 
        show_alert=True
    )

@router.message(Command("approve"))
async def manual_approve_cmd(message: Message):
    args = message.text.split()
    limit = int(args[1]) if len(args) > 1 and args[1].isdigit() else 100
    chat_id = message.chat.id
    user_ids = await db.get_pending_requests(channel_id=chat_id, limit=limit)

    if not user_ids:
        await message.reply("<b>❌ No pending requests found in queue for this channel.</b>", parse_mode="HTML")
        return

    status_msg = await message.reply(f"<b>⚡ Approving {len(user_ids)} requests...</b>", parse_mode="HTML")
    approved_count = 0
    approved_list = []

    for user_id in user_ids:
        try:
            await message.bot.approve_chat_join_request(chat_id=chat_id, user_id=user_id)
            approved_count += 1
            approved_list.append(user_id)
            await asyncio.sleep(0.04) 
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            try:
                await message.bot.approve_chat_join_request(chat_id=chat_id, user_id=user_id)
                approved_count += 1
                approved_list.append(user_id)
            except Exception:
                continue
        except Exception:
            continue

    await db.remove_pending_requests(channel_id=chat_id, user_ids=approved_list)
    await status_msg.edit_text(
        f"<b>✅ Batch Complete!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• <b>Approved:</b> <code>{approved_count}</code> users\n"
        f"• <b>Remaining:</b> <code>{len(user_ids) - approved_count}</code>",
        parse_mode="HTML"
        )
    
