import logging

from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery, User
from aiogram.fsm.context import FSMContext


class FSMFlagChecker(Filter):
    flag = None

    async def __call__(
        self, 
        obj: Message | CallbackQuery, 
        state: FSMContext,
        event_from_user: User
    ):
        data = await state.get_data()

        if self.flag is None:
            raise NotImplementedError('FSMFlagChecker.flag not overriden')
        
        flag_value = data.get(self.flag, None)
        if flag_value is None:
            logging.info(
                f'Не обнаружен флаг {self.flag} в стейте пользователя {event_from_user.full_name}'
            )

        return bool(flag_value)




