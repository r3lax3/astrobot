from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, User

from src import messages
from src.database import crud
from src.keyboards import bt, keyboards
from src.routers.states import MainMenu, Subscription

from .utils import get_subscription_status_text


r = Router()


@r.callback_query(MainMenu.prediction_access_denied, F.data == bt.subscription)
@r.callback_query(Subscription.period, F.data == bt.back_to_menu)
@r.callback_query(Subscription.get_promocode, F.data == bt.back)
async def subscription_menu_callback_query_handler(
    callback: CallbackQuery,
    state: FSMContext,
    event_from_user: User
):
    await subscription_menu(callback.message, state, event_from_user)


@r.message(F.text, F.text == bt.subscription)
async def subscription_menu(
    message: Message,
    state: FSMContext,
    event_from_user: User
):
    user = crud.get_user(user_id=event_from_user.id)
    subscription_status_text = get_subscription_status_text(user)

    bot_message = await message.answer(
        messages.SUBSCRITION_MENU.format(
            subscription_status=subscription_status_text
        ),
        reply_markup=keyboards.subscription_menu()
    )
    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(Subscription.chooose_action)
