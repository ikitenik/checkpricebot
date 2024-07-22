from services.user_states import UserState, set_state, get_state
from aiogram.types import Message
from aiogram.filters import BaseFilter
# смотрит состояние пользователя
class StateFilter(BaseFilter):
    def __init__(self, state: int):
        self.state = state

    async def __call__(self, message: Message) -> bool:
        if self.state == await get_state(message.from_user.id):
            return True
        # Если не нашли ни одного юзернейма, вернём False
        return False