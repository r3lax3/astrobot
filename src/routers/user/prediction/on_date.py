import datetime as dt
from datetime import datetime, timedelta

from aiogram import Bot, F, Router, exceptions
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message, User

from src import config, messages
from src.database import Database
from src.enums import FileName
from src.filters import HasPredictionAccess
from src.image_processing import get_image_with_astrodata
from src.keyboard_manager import KeyboardManager, bt
from src.models import DateModifier
from src.routers.states import MainMenu, Subscription
from src.routers.user.prediction.text_formatting import get_prediction_text
from src.utils import get_timezone_offset


DATETIME_FORMAT: str = config.get("database.datetime_format")
DATE_FORMAT: str = config.get("database.date_format")
DREAMS_INTERPRETATIONS_FILEPATH = "./dreams.csv"
PREDICTION_MENU_IMAGE = config.get("files.prediction_menu")
WAIT_STICKER = config.get("files.wait_sticker")

r = Router()


@r.callback_query(MainMenu.prediction_choose_date, F.data == bt.decline)
@r.callback_query(MainMenu.prediction_end, F.data == bt.back)
@r.callback_query(Subscription.action_end, F.data == bt.try_in_deal)
@r.callback_query(MainMenu.prediction_every_day_enter_time, F.data == bt.back)
async def get_prediction_callback_redirect(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User,
):
    await get_prediction(
        callback.message,
        state,
        keyboards,
        database,
        event_from_user
    )


@r.message(F.text, F.text == bt.prediction)
@r.message(F.text, F.text == bt.prediction_no_access)
async def get_prediction(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User,
):
    user = database.get_user(user_id=event_from_user.id)

    now = datetime.utcnow()
    current_user_subscription_end_date = datetime.strptime(
        user.subscription_end_date, DATETIME_FORMAT
    )

    if now < current_user_subscription_end_date:
        bot_message = await message.answer_photo(
            photo=PREDICTION_MENU_IMAGE,
            caption=messages.prediction_descr,
            reply_markup=keyboards.predict_choose_action
        )
        await state.set_state(MainMenu.prediction_choose_action)
        await state.update_data(
            prediction_access=True,
            subscription_end_date=user.subscription_end_date,
            del_messages=[bot_message.message_id],
        )
    else:
        await prediction_access_denied(message, state, keyboards)


@r.callback_query(
    MainMenu.prediction_end,
    F.data == bt.check_another_date,
    ~HasPredictionAccess()
)
@r.callback_query(
    MainMenu.prediction_choose_date,
    ~HasPredictionAccess()
)
async def prediction_access_denied_callback_handler(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager
):
    await prediction_access_denied(callback.message, state, keyboards)


@r.message(MainMenu.prediction_choose_action, ~HasPredictionAccess())
async def prediction_access_denied(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    bot_message = await message.answer(
        messages.prediction_access_denied,
        reply_markup=keyboards.prediction_access_denied,
    )
    await state.set_state(MainMenu.prediction_access_denied)
    await state.update_data(
        prediction_access=False, del_messages=[bot_message.message_id]
    )


@r.callback_query(MainMenu.prediction_end, F.data == bt.check_another_date)
async def prediction_ended_back(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager
):
    await prediction_on_date(callback.message, state, keyboards)


@r.message(
    MainMenu.prediction_choose_action,
    F.text, F.text == bt.prediction_for_date
)
async def prediction_on_date(
    message: Message, state: FSMContext, keyboards: KeyboardManager
):
    data = await state.get_data()
    today = dt.datetime.utcnow().date() + timedelta(hours=data["timezone_offset"])
    await state.update_data(
        date=today.strftime(DATE_FORMAT), today=today.strftime(DATE_FORMAT)
    )
    await update_prediction_date(message, state, keyboards)


@r.message(
    MainMenu.prediction_choose_action,
    F.text, F.text == bt.prediction_for_today
)
async def prediction_for_today(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User,
    bot: Bot,
):
    user = database.get_user(event_from_user.id)
    current_location = database.get_location(user.current_location_id)

    timezone_offset: int = get_timezone_offset(
        latitude=current_location.latitude, longitude=current_location.longitude
    )
    today_date = datetime.today() + datetime.timedelta(hours=timezone_offset)
    await state.update_data(date=today_date.strptime(today_date, DATE_FORMAT))

    await prediction_on_date_get_prediction(
        message,
        state,
        keyboards,
        database,
        event_from_user,
        bot
    )


# Confirmed
@r.callback_query(MainMenu.prediction_choose_date, F.data == bt.confirm)
async def prediction_on_date_get_prediction_callback_redirect(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User,
    bot: Bot,
):
    await prediction_on_date_get_prediction(
        callback.message,
        state,
        keyboards,
        database,
        event_from_user,
        bot
    )


async def prediction_on_date_get_prediction(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User,
    bot: Bot,
):
    data = await state.get_data()

    # Getting user
    user = database.get_user(event_from_user.id)

    subscription_end_date = datetime.strptime(
        user.subscription_end_date, DATETIME_FORMAT
    )
    target_date_str: str = data["date"]
    target_date = datetime.strptime(target_date_str, DATE_FORMAT)
    timezone_offset = timedelta(hours=data["timezone_offset"])

    if subscription_end_date + timezone_offset > target_date:
        wait_message = await message.answer(messages.wait)
        sticker_message = await message.answer_sticker(WAIT_STICKER)

        text = await get_prediction_text(
            date=target_date, database=database, user_id=event_from_user.id
        )

        photo_bytes = get_image_with_astrodata(user, database, date=target_date)

        photo = BufferedInputFile(file=photo_bytes, filename=FileName.PREDICTION.value)

        for msg in [wait_message, sticker_message]:
            try:
                await bot.delete_message(event_from_user.id, msg.message_id)
            except exceptions.TelegramBadRequest:
                continue

        await message.answer_photo(photo=photo)
        prediction_message = await message.answer(
            text=text,
            reply_markup=keyboards.predict_completed
        )

        await state.update_data(
            delete_keyboard_message_id=prediction_message.message_id,
            last_prediction_message_id=prediction_message.message_id
        )
        await state.set_state(MainMenu.prediction_end)
    else:
        bot_message = await message.answer(messages.not_enough_subscription)
        await update_prediction_date(bot_message, state, keyboards)


# Updating date
@r.callback_query(MainMenu.prediction_choose_date)
async def prediction_update_date_callback_handler(
    callback: CallbackQuery, state: FSMContext, keyboards: KeyboardManager
):
    data = await state.get_data()

    date = data["date"]
    date = datetime.strptime(date, DATE_FORMAT)
    modified_date = date + timedelta(days=DateModifier.unpack(callback.data).modifier)

    await state.update_data(date=modified_date.strftime(DATE_FORMAT))
    await update_prediction_date(callback.message, state, keyboards)


async def update_prediction_date(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    data = await state.get_data()

    date = data["date"]
    today = data["today"]
    date_message = await message.answer(
        messages.prediction_at_date.format(today=today),
        reply_markup=keyboards.predict_choose_date(date),
    )

    prediction_message_id = data.get("last_prediction_message_id", None)

    if message.message_id != prediction_message_id:
        await state.update_data(
            del_messages=[
                date_message.message_id,
                message.message_id
            ]
        )

    else:
        await state.update_data(del_messages=[date_message.message_id])

    await state.set_state(MainMenu.prediction_choose_date)
