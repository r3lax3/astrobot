from aiogram import Router, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest

from src import config, messages
from src.keyboard_manager import KeyboardManager, bt
from src.routers.states import MainMenu, Subscription


r = Router()
MAIN_MENU_IMAGE: str = config.get('files.main_menu')
print(f'{MAIN_MENU_IMAGE = }')


@r.message(
    MainMenu.prediction_choose_action, 
    F.text,
    F.text == bt.back
)
@r.message(F.text, F.text == bt.main_menu)
@r.message(Command(commands=['menu']))
async def main_menu(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    bot: Bot
):
    data = await state.get_data()

    main_menu_message_id = data.get('main_menu_message_id', None)

    if main_menu_message_id is not None:
        try:
            await bot.delete_message(
                chat_id=message.chat.id, 
                message_id=main_menu_message_id
            )
        except TelegramBadRequest:
            pass

    if data['prediction_access']:
        keyboard = keyboards.main_menu
    else:
        keyboard = keyboards.main_menu_prediction_no_access

    if data['first_time']:
        text = messages.main_menu_first_time
        await state.update_data(first_time=False)

    else:
        text = messages.main_menu
    print(f'{text = }')

    main_menu_message = await message.answer_photo(
        photo=MAIN_MENU_IMAGE,
        caption=text,
        reply_markup=keyboard
    )
    await state.update_data(
        del_messages=[message.message_id], 
        main_menu_message_id=main_menu_message.message_id
    )
    await state.set_state(MainMenu.choose_action)


@r.callback_query(F.data == bt.main_menu)
@r.callback_query(Subscription.period, F.data == bt.back)
async def to_main_menu_button_handler(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    bot: Bot
):
    await main_menu(callback.message, state, keyboards, bot)

