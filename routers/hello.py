from aiogram import Bot, Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from states.welcome_states import Welcome
from db.database import get_usd_price

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await state.set_state(Welcome.name)
    await message.answer(
        f"Добрый день. Как вас зовут?"
    )

@router.message(F.text, Welcome.name)
async def get_user_name(message: Message, state: FSMContext, bot: Bot):
    usd_rate = await get_usd_price()
    await message.answer(
        f"Рад знакомству, {message.text}! Курс доллара сегодня {usd_rate:.2f} р."
    )