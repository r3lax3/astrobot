from datetime import datetime, timedelta

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, User

from src import config, messages
from src.database import crud, Session
from src.database.models import Location
from src.database.models import User as DBUser
from src.enums import Gender, LocationType
from src.keyboards import keyboards
from src.keyboard_manager import bt, buttons_text
from src.routers.states import ProfileSettings
from src.routers.user.main_menu import main_menu
from src.scheduler import EveryDayPredictionScheduler
from src.utils import get_location_by_coords, get_timezone_offset


DATETIME_FORMAT: str = config.get("database.datetime_format")
SUBSCRIPTION_TEST_PERIOD: int = config.get("subscription.test_period_in_days")
PROFILE_IMAGE = config.get("files.profile")

r = Router()


@r.callback_query(ProfileSettings.choose_gender, F.data == bt.back)
@r.callback_query(ProfileSettings.get_new_name, F.data == bt.back)
@r.callback_query(F.data == bt.profile_settings)
async def profile_settings_menu_callback_handler(
    callback: CallbackQuery,
    state: FSMContext,
    event_from_user: User
):
    await profile_settings_menu(callback.message, state, event_from_user)


@r.message(F.text, F.text == bt.profile_settings)
async def profile_settings_menu(
    message: Message,
    state: FSMContext,
    event_from_user: User
):
    user = crud.get_user(event_from_user.id)

    bot_message = await message.answer_photo(
        photo=PROFILE_IMAGE,
        caption=messages.PROFILE_SETTINGS.format(
            name=user.name,
            user_id=event_from_user.id,
            current_location_title=user.current_location.title,
            birth_datetime=user.birth_datetime,
            birth_location_title=user.birth_location.title,
        ),
        reply_markup=keyboards.profile_settings(),
    )
    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(ProfileSettings.choose_option)


# Name
@r.callback_query(ProfileSettings.choose_option, F.data == bt.name)
async def change_name(
    callback: CallbackQuery,
    state: FSMContext,
    database,
    event_from_user: User,
):
    user = database.get_user(event_from_user.id)
    bot_message = await callback.message.answer(
        messages.CHANGE_NAME.format(name=user.name),
        reply_markup=keyboards.back()
    )
    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(ProfileSettings.get_new_name)


# Gender
@r.callback_query(ProfileSettings.choose_option, F.data == bt.gender)
async def choose_gender(
    callback: CallbackQuery,
    state: FSMContext,
    database,
):
    user = database.get_user(user_id=callback.from_user.id)

    if user.gender is not None:
        bot_message = await callback.message.answer(
            messages.CHOOSE_GENDER.format(gender=buttons_text[user.gender]),
            reply_markup=keyboards.choose_gender(),
        )
    else:
        bot_message = await callback.message.answer(
            messages.GENDER_NOT_CHOOSEN,
            reply_markup=keyboards.choose_gender()
        )

    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(ProfileSettings.choose_gender)


@r.callback_query(ProfileSettings.choose_gender, F.data == bt.male)
async def gender_is_male(
    callback: CallbackQuery,
    state: FSMContext,
    database,
):
    database.change_user_gender(
        gender=Gender.male.value,
        user_id=callback.from_user.id
    )
    await choose_gender(callback, state, database)


@r.callback_query(ProfileSettings.choose_gender, F.data == bt.female)
async def gender_is_female(
    callback: CallbackQuery,
    state: FSMContext,
    database,
):
    database.change_user_gender(
        gender=Gender.female.value,
        user_id=callback.from_user.id
    )
    await choose_gender(callback, state, database)


# Current Location
@r.callback_query(ProfileSettings.choose_option, F.data == bt.change_timezone)
async def change_timezone(
    callback: CallbackQuery,
    state: FSMContext
):
    await enter_current_location(callback.message, state)


async def enter_current_location(message: Message, state: FSMContext):
    data = await state.get_data()

    first_time = data.get("first_time", True)

    if not first_time:
        bot_message = await message.answer(
            messages.ENTER_NEW_CURRENT_LOCATION,
            reply_markup=keyboards.to_main_menu()
        )
    else:
        bot_message = await message.answer(messages.ENTER_CURRENT_LOCATION)

    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(ProfileSettings.get_current_location)


@r.message(ProfileSettings.get_current_location, F.location)
async def get_current_location(message: Message, state: FSMContext):
    data = await state.get_data()

    longitude = message.location.longitude
    latitude = message.location.latitude

    current_location_title = get_location_by_coords(
        longitude=longitude,
        latitude=latitude
    )

    if data.get('first_time', False):
        bot_message = await message.answer(
            messages.GET_CURRENT_LOCATION_CONFIRM_FIRST_TIME.format(
                current_location=current_location_title
            ),
            reply_markup=keyboards.confirm(),
        )

    else:
        bot_message = await message.answer(
            messages.GET_CURRENT_LOCATION_CONFIRM.format(
                current_location=current_location_title
            ),
            reply_markup=keyboards.confirm(),
        )

    await state.update_data(
        del_messages=[bot_message.message_id, message.message_id],
        current_location={"latitude": latitude, "longitude": longitude},
        current_location_title=current_location_title,
    )
    await state.set_state(ProfileSettings.location_confirm)


@r.message(ProfileSettings.get_current_location)
async def get_current_location_error(
    message: Message,
    state: FSMContext,
):
    bot_message = await message.answer(messages.NOT_LOCATION)
    await enter_current_location(bot_message, state)


@r.callback_query(ProfileSettings.location_confirm, F.data == bt.decline)
async def get_current_location_not_confirmed(
    callback: CallbackQuery,
    state: FSMContext
):
    await enter_current_location(callback.message, state)


@r.callback_query(ProfileSettings.location_confirm, F.data == bt.confirm)
async def get_current_location_confirmed(
    callback: CallbackQuery,
    state: FSMContext,
    database,
    event_from_user: User,
    bot: Bot,
    scheduler: EveryDayPredictionScheduler,
):
    data = await state.get_data()

    name = data["name"]
    current_location = data["current_location"]
    current_location_title = data["current_location_title"]
    with Session() as session:
        if data.get("first_time", False):
            birth_datetime = data["birth_datetime"]
            birth_location = data["birth_location"]
            birth_location_title = data["birth_location_title"]

            now = datetime.utcnow()
            test_period_end = now + timedelta(days=SUBSCRIPTION_TEST_PERIOD)

            crud.add_user(
                session,
                DBUser(
                    user_id=event_from_user.id,
                    name=name,
                    birth_datetime=birth_datetime,
                    birth_location=Location(
                        type=LocationType.birth.value,
                        **birth_location,
                        title=birth_location_title
                    ),
                    current_location=Location(
                        type=LocationType.current.value,
                        **current_location,
                        title=current_location_title
                    ),
                    subscription_end_date=test_period_end.strftime(
                        DATETIME_FORMAT
                    ),
                    timezone_offset=get_timezone_offset(**current_location),
                    every_day_prediction_time="8:30",
                )
            )

            await scheduler.set_all_jobs(user_id=event_from_user.id)

            await state.update_data(
                prediction_access=True,
                subscription_end_date=test_period_end.strftime(DATETIME_FORMAT),
                timezone_offset=get_timezone_offset(**current_location),
            )

            await main_menu(callback.message, state, bot)

        else:
            crud.update_user_current_location(
                session,
                event_from_user.id,
                Location(
                    type=LocationType.current.value,
                    **current_location,
                    title=get_location_by_coords(**current_location)
                ),
            )
            crud.update_user(
                event_from_user.id,
                timezone_offset=get_timezone_offset(**current_location)
            )
            await profile_settings_menu_callback_handler(
                callback,
                state,
                event_from_user
            )
            await scheduler.set_all_jobs(user_id=event_from_user.id)
