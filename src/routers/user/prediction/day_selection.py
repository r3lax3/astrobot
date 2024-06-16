from aiogram import F, Router, exceptions
from aiogram.types import Message, CallbackQuery, User
from aiogram.fsm.context import FSMContext

from src import config, messages
from src.database import Session, crud
from src.filters.subscription import HaveActiveSubscription
from src.keyboards import bt, keyboards
from src.routers.states import MainMenu
from src.common import DAY_SELECTION_DATABASE

from .text_formatting import get_formatted_selected_days


WAIT_STICKER = config.get("files.wait_sticker")
DAY_SELECTION_ACTION_CATEGORIES = list(DAY_SELECTION_DATABASE.keys())

r = Router()


@r.message(F.text == bt.day_selection)
async def day_selection_handler(
    message: Message,
    state: FSMContext,
    event_from_user: User
):
    with Session() as session:
        user = crud.get_user(event_from_user.id, session)

        bot_message = await message.answer(
            messages.CHOOSE_DAY_SELECTION_ACTION_CATEGORY.format(
                name=user.name
            ),
            reply_markup=keyboards.day_selection_categories(
                DAY_SELECTION_ACTION_CATEGORIES
            )
        )
        await state.update_data(del_messages=[bot_message.message_id])
        await state.set_state(MainMenu.day_selection_get_category)


@r.callback_query(MainMenu.day_selection_get_category)
async def day_selection_get_category(
    callback: CallbackQuery,
    state: FSMContext,
    event_from_user: User
):
    await state.update_data(day_selection_category=callback.data)
    await enter_day_selection_action(callback, state, event_from_user)


@r.callback_query(F.data == bt.choose_another_action)
async def enter_day_selection_action(
    callback: CallbackQuery,
    state: FSMContext,
    event_from_user: User
):
    data = await state.get_data()

    category = data['day_selection_category']

    action_list = list(DAY_SELECTION_DATABASE[category].keys())
    with Session() as session:
        user = crud.get_user(event_from_user.id, session)

        bot_message = await callback.message.answer(
            messages.DAY_SELECTION_CHOOSE_ACTION.format(name=user.name),
            reply_markup=keyboards.day_selection_actions(action_list)
        )
        await state.update_data(del_messages=[bot_message.message_id])
        await state.set_state(MainMenu.day_selection_get_action)


@r.callback_query(
    MainMenu.day_selection_get_action,
    HaveActiveSubscription()
)
async def day_selection_get_action(
    callback: CallbackQuery,
    state: FSMContext,
    event_from_user: User
):
    data = await state.get_data()

    category = data['day_selection_category']
    action = callback.data

    favorably = DAY_SELECTION_DATABASE[category][action]['favorably']

    with Session() as session:
        user = crud.get_user(event_from_user.id, session)
        activated_promocodes_list = crud.get_promocodes(
            session,
            activated_by=event_from_user.id
        )
        is_user_client = len(activated_promocodes_list) > 0

        wait_message = await callback.message.answer(
            messages.WAIT_DAY_SELECTION
        )
        sticker_message = await callback.message.answer_sticker(WAIT_STICKER)

        selected_days = get_formatted_selected_days(category, action, user)

        for msg in [wait_message, sticker_message]:
            try:
                await msg.delete()
            except exceptions.TelegramBadRequest:
                continue

        if selected_days:
            if favorably:
                bot_message = await callback.message.answer(
                    messages.DAY_SELECTION_SUCCESS_FAVORABLY.format(
                        name=user.name,
                        action=action,
                        selected_days=selected_days
                    ),
                    reply_markup=keyboards.day_selection_success()
                )
            else:
                bot_message = await callback.message.answer(
                    messages.DAY_SELECTION_SUCCESS_UNFAVORABLY.format(
                        name=user.name,
                        action=action,
                        selected_days=selected_days
                    ),
                    reply_markup=keyboards.day_selection_success()
                )
        else:
            if is_user_client:
                bot_message = await callback.message.answer(
                    messages.DAY_SELECTION_FAILED_CLIENT.format(
                        name=user.name
                    ),
                    reply_markup=keyboards.day_selection_failed()
                )
            else:
                bot_message = await callback.message.answer(
                    messages.DAY_SELECTION_FAILED_TRIAL.format(
                        name=user.name
                    ),
                    reply_markup=keyboards.day_selection_failed()
                )
        await state.update_data(
            delete_keyboard_message_id=bot_message.message_id
        )
        await state.set_state(MainMenu.end_action)


@r.callback_query(MainMenu.day_selection_get_action)
async def prediction_access_denied(
    callback: CallbackQuery,
    state: FSMContext,
    event_from_user: User
):
    with Session() as session:
        user = crud.get_user(event_from_user.id, session)
        bot_message = await callback.message.answer(
            messages.DAY_SELECTION_NO_ACCESS.format(
                name=user.name
            ),
            reply_markup=keyboards.day_selection_no_access(),
        )
        await state.set_state(MainMenu.end_action)
        await state.update_data(
            prediction_access=False,
            del_messages=[bot_message.message_id]
        )
