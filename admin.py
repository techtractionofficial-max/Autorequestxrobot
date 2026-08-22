import asyncio
import io
import time
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError, TelegramBadRequest
from database import db
from keyboards import parse_broadcast_buttons, get_admin_panel_keyboard
from config import config

router = Router()

class BroadcastState(StatesGroup):
    waiting_for_content = State()
    confirm_dispatch = State()

@router.callback_query(F.data == "admin_broadcast", F.from_user.id.in_(config.ADMIN_IDS))
async def start_broadcast(call: CallbackQuery, state: FSMContext):
    instruction = (
        "<b>📢 Rich-Media Broadcast Dispatcher</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Send the message, photo, or video you wish to broadcast.\n\n"
        "<b>🔘 Custom Inline Button Syntax:</b>\n"
        "Append your button definitions at the end of the text/caption:\n"
        "<code>[ Visit Website | https://example.com ]</code>\n"
        "<code>[ Join Channel | https://t.me/channel ] [ Support | https://t.me/help ]</code>"
    )
    await call.message.edit_text(instruction, parse_mode="HTML")
    await state.set_state(BroadcastState.waiting_for_content)
    await call.answer()

@router.message(BroadcastState.waiting_for_content, F.from_user.id.in_(config.ADMIN_IDS))
async def process_broadcast_preview(message: Message, state: FSMContext):
    caption = message.caption or message.text or ""
    clean_text, reply_markup = parse_broadcast_buttons(caption)
    
    await state.update_data(
        message_id=message.message_id,
        chat_id=message.chat.id,
        clean_text=clean_text,
        has_buttons=bool(reply_markup)
    )

    await message.answer("<b>👁️ Previewing Broadcast Output:</b>", parse_mode="HTML")
    
    # Render preview
    if message.photo:
        await message.answer_photo(
            photo=message.photo[-1].file_id,
            caption=clean_text,
            parse_mode="HTML",
            reply_markup=reply_markup
        )
    elif message.video:
        await message.answer_video(
            video=message.video.file_id,
            caption=clean_text,
            parse_mode="HTML",
            reply_markup=reply_markup
        )
    else:
        await message.answer(
            text=clean_text,
            parse_mode="HTML",
            reply_markup=reply_markup
        )

    users = await db.get_all_active_users()
    confirm_text = (
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>Audience Size:</b> <code>{len(users)}</code> active nodes\n"
        f"⚡ <b>Estimated Time:</b> <code>~{round(len(users) / 25, 1)}s</code>\n\n"
        f"<i>Reply <code>YES</code> to confirm dispatch, or <code>CANCEL</code> to abort.</i>"
    )
    await message.answer(confirm_text, parse_mode="HTML")
    await state.set_state(BroadcastState.confirm_dispatch)

@router.message(BroadcastState.confirm_dispatch, F.text.casefold() == "yes", F.from_user.id.in_(config.ADMIN_IDS))
async def execute_broadcast(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    users = await db.get_all_active_users()
    total_users = len(users)
    
    if total_users == 0:
        await message.answer("<b>❌ Target audience is empty.</b>", parse_mode="HTML")
        return

    progress_msg = await message.answer(
        "<b>🚀 Initializing High-Speed Broadcast Engine...</b>",
        parse_mode="HTML"
    )

    sent = 0
    blocked = 0
    failed = 0
    start_time = time.time()
    last_update_time = time.time()

    for idx, user_id in enumerate(users, start=1):
        try:
            await message.bot.copy_message(
                chat_id=user_id,
                from_chat_id=data["chat_id"],
                message_id=data["message_id"]
            )
            sent += 1
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            try:
                await message.bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=data["chat_id"],
                    message_id=data["message_id"]
                )
                sent += 1
            except Exception:
                failed += 1
        except (TelegramForbiddenError, TelegramBadRequest):
            blocked += 1
            await db.set_user_active_status(user_id, is_active=False)
        except Exception:
            failed += 1

        # Smooth pacing to respect limits (~25 req/sec)
        await asyncio.sleep(config.BROADCAST_DELAY_SECONDS)

        # Update progress board every 3 seconds
        if time.time() - last_update_time > 3.0 or idx == total_users:
            last_update_time = time.time()
            elapsed = max(time.time() - start_time, 0.1)
            speed = round(sent / elapsed, 1)
            percentage = round((idx / total_users) * 100, 1)

            progress_bar = "█" * int(percentage // 10) + "░" * (10 - int(percentage // 10))
            
            dashboard = (
                f"<b>🚀 Broadcast in Progress</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"<b>Progress:</b> <code>[{progress_bar}] {percentage}%</code>\n\n"
                f"• <b>Delivered:</b> <code>{sent}</code>\n"
                f"• <b>Blocked/Dead:</b> <code>{blocked}</code>\n"
                f"• <b>Failed:</b> <code>{failed}</code>\n"
                f"• <b>Throughput:</b> <code>{speed} msg/sec</code>\n"
                f"• <b>Processed:</b> <code>{idx}/{total_users}</code>"
            )
            try:
                await progress_msg.edit_text(dashboard, parse_mode="HTML")
            except Exception:
                pass

    total_time = round(time.time() - start_time, 2)
    final_report = (
        f"<b>✅ Broadcast Operation Completed!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• <b>Total Targets:</b> <code>{total_users}</code>\n"
        f"• <b>Successfully Delivered:</b> <code>{sent}</code>\n"
        f"• <b>Dead Nodes Pruned:</b> <code>{blocked}</code>\n"
        f"• <b>Unreachable:</b> <code>{failed}</code>\n"
        f"• <b>Total Elapsed Time:</b> <code>{total_time}s</code>"
    )
    await progress_msg.edit_text(final_report, parse_mode="HTML")

@router.callback_query(F.data == "admin_export_users", F.from_user.id.in_(config.ADMIN_IDS))
async def export_users_csv(call: CallbackQuery):
    users = await db.get_all_active_users()
    data_buffer = io.BytesIO("\n".join(str(uid) for uid in users).encode("utf-8"))
    
    file = BufferedInputFile(
        file=data_buffer.getvalue(),
        filename=f"users_export_{int(time.time())}.txt"
    )
    
    await call.message.answer_document(
        document=file,
        caption=f"<b>📁 Total Exported Active User IDs:</b> <code>{len(users)}</code>",
        parse_mode="HTML"
    )
    await call.answer()
  
