from aiogram.fsm.state import StatesGroup, State


class Form(StatesGroup):
    pair_choice = State()
    waiting_for_pair= State()
    order_pair = State()
    order_type = State()
    order_price = State()
    waiting_for_amount = State()
    close_position_pairs = State()
    close_position = State()
    notify = State()