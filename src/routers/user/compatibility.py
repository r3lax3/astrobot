from aiogram import Router, F

from aiogram.types import Message, User
from aiogram.fsm.context import FSMContext

from src.routers import messages
from src.keyboard_manager import KeyboardManager, bt
from src.database.database import Database, User as DBUser


r = Router()


@r.message(F.text == bt.compability)
async def compability_menu(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User
):
    user: DBUser = database.get_user(user_id=event_from_user.id)
    if user.gender is not None:
        # TODO
        bot_message = await message.answer(
            'Функционал ещё не готов, подождите некоторое время когда разработчик его добавит.',
            reply_markup=keyboards.to_main_menu
        )
    else:
        bot_message = await message.answer(
            messages.gender_not_choosen,
            reply_markup=keyboards.gender_not_choosen
        )
    await state.update_data(del_messages=[bot_message.message_id])

