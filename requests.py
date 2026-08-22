import asyncio
from aiogram import Router, F
from aiogram.types import ChatJoinRequest, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError
from database import db

router = Router()

@router.chat_join_request()
async def join_request_handler(event: ChatJoinRequest):
    """Listens for join requests, registers user, triggers promo DM, and auto-approves."""
    user = event.from_user
    chat = event.chat

    # 1. Register or update user in database
    await db.register_user(
        user_id=user.id,
        first_name=user.first_name,
        username=user.username
    )

    # 2. Retrieve channel settings
    channel_data = await db.get_channel(chat.id)
    
    if not channel_data:
        # Default auto-save channel configuration
        await db.add_channel(channel_id=chat.id, owner_id=user.id, title=chat.title)
        auto_approve = 1
        custom_dm = "<b>Hello {name}!</b> 🎉\n\nYour request has been approved.\nJoin our exclusive channel below:"
        btn_text = "🔥 Join VIP Channel"
        btn_url = "https://t.me/Telegram"
    else:
        _, _, _, auto_approve, custom_dm, btn_text, btn_url = channel_data

    # 3. Deliver Promotional Direct Message
    try:
        promo_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=btn_text, url=btn_url)]]
        )
        formatted_dm = custom_dm.replace("{name}", user.first_name or "there")
        await event.bot.send_message(
            chat_id=user.id,
            text=formatted_dm,
            parse_mode="HTML",
            reply_markup=promo_keyboard
        )
    except (TelegramForbiddenError, Exception):
        pass  # User has blocked DMs from bots

    # 4. Handle Approval / Queuing
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

@router.message(Command("approve"))
async def manual_approve_cmd(message: Message):
    """Executes high-speed batch approval for stored requests."""
    args = message.text.split()
    limit = int(args[1]) if len(args) > 1 and args[1].isdigit() else 100

    chat_id = message.chat.id
    user_ids = await db.get_pending_requests(channel_id=chat_id, limit=limit)

    if not user_ids:
        await message.reply("<b>❌ No pending requests found in queue for this channel.</b>", parse_mode="HTML")
        return

    status_msg = await message.reply(
        f"<b>⚡ Approving {len(user_ids)} requests...</b>",
        parse_mode="HTML"
    )

    approved_count = 0
    approved_list = []

    for user_id in user_ids:
        try:
            await message.bot.approve_chat_join_request(chat_id=chat_id, user_id=user_id)
            approved_count += 1
            approved_list.append(user_id)
            await asyncio.sleep(0.04)  # Safe speed rate limiter
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
  
