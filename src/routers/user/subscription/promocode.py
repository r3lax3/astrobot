from datetime import timedelta

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, User

from src import config, messages
from src.database import crud
from src.keyboards import bt, keyboards, callback_data
from src.scheduler import EveryDayPredictionScheduler
from src.enums import PromocodeStatus
from src.routers.states import Subscription
from src.dicts import MONTHS_TO_STR_MONTHS
from src.utils import delete_message


DATETIME_FORMAT = config.get("database.datetime_format")
DATE_FORMAT = config.get("database.date_format")

PROMOCODE_IMAGE: str = config.get("files.promocode")

r = Router()


# "ENTER PROMOCODE" MENU
@r.callback_query(Subscription.get_activate_promocode_confirm, F.data == bt.back)
@r.callback_query(Subscription.action_end, F.data == bt.back_to_menu)
@r.callback_query(Subscription.chooose_action, F.data == bt.enter_promocode)
async def enter_promocode_menu_callback_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    await enter_promocode_menu(callback.message, state)


async def enter_promocode_menu(
    message: Message,
    state: FSMContext
):
    bot_message = await message.answer_photo(
        photo=PROMOCODE_IMAGE,
        caption=messages.ENTER_PROMOCODE,
        reply_markup=keyboards.back()
    )
    await state.update_data(
        del_messages=[
            bot_message.message_id,
            message.message_id
        ]
    )
    await state.set_state(Subscription.get_promocode)


# GET PROMOCODE
@r.message(Subscription.get_promocode, F.text)
async def get_promocode(
    message: Message,
    state: FSMContext,
):
    await state.update_data(promocode=message.text)
    await enter_activate_promocode_confirm(message, state)


@r.callback_query(callback_data.Promocode.filter())
async def enter_activate_promocode_confirm_callback_handler(
    callback: CallbackQuery,
    callback_data: callback_data.Promocode,
    state: FSMContext,
):
    await state.update_data(promocode=callback_data.promocode)

    await delete_message(callback.message)

    await enter_activate_promocode_confirm(callback.message, state)


async def enter_activate_promocode_confirm(
    message: Message,
    state: FSMContext
):
    data = await state.get_data()

    promocode_str = data.get("promocode", None)
    promocode = crud.get_promocode(promocode_str)

    if promocode is not None:
        if promocode.is_activated:
            status = PromocodeStatus.activated
        else:
            status = PromocodeStatus.not_activated

        bot_message = await message.answer(
            messages.GET_ACTIVATE_PROMOCODE_CONFIRM.format(
                promocode=promocode_str,
                period=MONTHS_TO_STR_MONTHS.get(promocode.period, "Ошибка"),
                status=status.value,
            ),
            reply_markup=keyboards.get_activate_promocode_confirm(),
        )
        await state.update_data(
            del_messages=[bot_message.message_id],
            is_activated=promocode.is_activated,
            period=promocode.period,
        )
        await state.set_state(Subscription.get_activate_promocode_confirm)

    else:
        await get_promocode_error(message, state)


@r.message(Subscription.get_promocode)
async def get_promocode_error(
    message: Message,
    state: FSMContext
):
    bot_message = await message.answer(messages.NOT_PROMOCODE)
    await enter_promocode_menu(bot_message, state)


# GET PROMOCODE ACTIVATION CONFIRM
@r.callback_query(
    Subscription.get_activate_promocode_confirm,
    F.data == bt.activate_promocode
)
async def activate_promocode(
    callback: CallbackQuery,
    state: FSMContext,
    database,
    event_from_user: User,
    scheduler: EveryDayPredictionScheduler
):
    data = await state.get_data()

    promocode_str = data["promocode"]
    is_promocode_activated: bool = data["is_activated"]
    period = data["period"]

    if not is_promocode_activated:
        database.add_period_to_subscription_end_date(
            user_id=event_from_user.id,
            period=timedelta(days=period * 30)
        )
        database.update_promocode(
            promocode_str=promocode_str,
            is_activated=True,
            activated_by=event_from_user.id,
        )
        await scheduler.set_all_jobs(event_from_user.id)
        bot_message = await callback.message.answer(
            messages.PROMOCODE_ACTIVATED,
            reply_markup=keyboards.promocode_activated()
        )
        await state.update_data(
            del_messages=[bot_message.message_id],
            prediction_access=True
        )
        await state.set_state(Subscription.action_end)
    else:
        bot_message = await callback.message.answer(
            messages.PROMOCODE_ALREADY_ACTIVATED,
            reply_markup=keyboards.back()
        )
        await state.update_data(del_messages=[bot_message.message_id])
