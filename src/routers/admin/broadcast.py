import asyncio
import logging

from datetime import datetime, timedelta
from typing import Optional

from aiogram import Router, Bot, exceptions, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src import config, messages
from src.database import Database
from src.keyboards import KeyboardManager, bt
from src.states import AdminStates


class NoBroadcastDataError(Exception):
    pass


r = Router()
datetime_format = config.get('database.datetime_format')


@r.callback_query(AdminStates.choose_action, F.data == bt.broadcast)
@r.callback_query(AdminStates.broadcast_get_confirm, F.data == bt.no_back)
async def create_distribution(
    callback: CallbackQuery, 
    state: FSMContext, 
    keyboards: KeyboardManager
):
    del_message = await callback.message.answer(
        messages.get_message_for_broadcast,
        reply_markup=keyboards.back_to_adminpanel
    )
    await state.update_data(del_messages=[del_message.message_id])
    await state.set_state(AdminStates.broadcast_get_message)


@r.message(AdminStates.broadcast_get_message)
async def get_distribution_message(
    message: Message, 
    state: FSMContext, 
    keyboards: KeyboardManager
):
    if message.photo:
        photo_file_id = message.photo[-1].file_id
        text = message.caption
    else:
        photo_file_id = None
        text = message.text
    
    if photo_file_id is None and text is not None:
        del_message1 = await message.answer(
            messages.broadcast_message_type_not_supported
        )
    else:
        del_message1 = await message.answer_photo(
            photo=photo_file_id,
            caption=text
        )

    if text is None and photo_file_id is None:
        del_message = await message.answer(
            messages.broadcast_message_type_not_supported,
            reply_markup=keyboards.back_to_adminpanel
        )
        await state.update_data(del_messages=[del_message.message_id])
        return

    del_message2 = await message.answer(
        messages.broadcast_msg_confirm,
        reply_markup=keyboards.yes_or_no
    )

    await state.update_data(
        broadcast_photo_file_id=photo_file_id,
        broadcast_text=text,
        del_messages=[
            del_message1.message_id,
            del_message2.message_id,
            message.message_id
        ]
    )
    await state.set_state(AdminStates.broadcast_get_confirm)


@r.callback_query(AdminStates.broadcast_get_confirm, F.data == bt.answer_yes)
async def sending_distribution_confirmed(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    keyboards: KeyboardManager,
    database: Database
):
    del_message = await callback.message.answer(
        messages.broadcast_started,
        reply_markup=keyboards.back_to_adminpanel
    )
    await state.update_data(
        del_messages=[del_message.message_id]
    )
    await state.set_state(AdminStates.action_end)

    data = await state.get_data()

    users_ids: list = [
        user.user_id 
        for user in await database.get_all_users()
    ]
    
    now = datetime.utcnow()
    now_in_Moskow = now + timedelta(hours=3)
    broadcast_start_date_Moskow = str(now_in_Moskow.strftime(datetime_format))

    count = await broadcast(
        bot,
        users_ids,
        photo_file_id=data['broadcast_photo_file_id'],
        text=data['broadcast_text']
    )

    dead_users = len(users_ids) - count
    active_users = max(len(users_ids) - dead_users, 0)


    now = datetime.utcnow()
    now_in_Moskow = now + timedelta(hours=3)
    broadcast_end_date_Moskow = str(now_in_Moskow.strftime(datetime_format))

    bot_message = await callback.message.answer(
        text=messages.broadcast_statistic.format(
            dead_users=dead_users,
            active_users=active_users,
            broadcast_start_date_Moskow=broadcast_start_date_Moskow,
            broadcast_end_date_Moskow=broadcast_end_date_Moskow
        )
    )
    data = await state.get_data()
    del_messages: list = data.get('del_messages', [])

    await state.update_data(
        del_messages=del_messages + [bot_message.message_id]
    )


async def send_message(
    bot: Bot,
    user_id: int,
    photo_file_id: Optional[str],
    text: Optional[str]
) -> bool:
    if photo_file_id is None and text is None:
        raise NoBroadcastDataError()
    try:
        if photo_file_id is None:
            await bot.send_message(
                chat_id=user_id,
                text=text
            )
        else:
            await bot.send_photo(
                photo=photo_file_id,
                chat_id=user_id,
                caption=text
            )

            
    except exceptions.TelegramRetryAfter as e:
        logging.info(f"Target [ID:{user_id}]: Flood limit is exceeded. Sleep {e.retry_after} seconds.")
        await asyncio.sleep(e.retry_after)
        await send_message(bot, user_id, photo_file_id, text)  # Recursive call
    except (exceptions.TelegramAPIError, exceptions.TelegramForbiddenError, exceptions.TelegramBadRequest):
        logging.info(f"Target [ID:{user_id}]: failed")
    else:
        logging.info(f"Target [ID:{user_id}]: success")
        return True
    return False


async def broadcast(
    bot: Bot,
    user_ids: list[int],
    photo_file_id: Optional[str],
    text: Optional[str]
) -> int:
    successes_count = 0
    try:
        for user_id in user_ids:
            if await send_message(
                bot,
                user_id,
                photo_file_id,
                text
            ):
                successes_count += 1
            await asyncio.sleep(0.1)  # 10 messages per second (Limit: 30 messages per second)

    finally:
        logging.info(f"{successes_count} messages successful sent.")
    return successes_count

