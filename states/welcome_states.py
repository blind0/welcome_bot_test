from aiogram.fsm.state import State, StatesGroup

class Welcome(StatesGroup):
    name = State()