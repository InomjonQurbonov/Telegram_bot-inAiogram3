import pandas as pd
from aiogram import Router
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message


from keyboards.pair_keyboard import make_pairs_buttons, make_order_buttons
from bybit_api_user import get_pairs, pair_order, monitor_and_closing
from state.form_states import Form

cmd_router = Router()
user_orders = {}

@cmd_router.message(CommandStart())
async def cmd_start(message: Message):
    s = "👋 Добро пожаловать! Я бот для управления валютными парами.\n\n" \
        "Вот что я могу делать:\n" \
        "\t - 📈 Узнать последнюю цену и ключевые данные по выбранной валютной паре (например, BTC/USDT).\n" \
        "\t - 📝 Разместить ордер на валютную пару.\n" \
        "\t - 📊 Автоматически закрыть позицию, если прибыль достигнет 0,1%.\n" \
        "\t - 🔔 Уведомить вас о закрытии позиции.\n\n" \
        "\t Введите /help, чтобы увидеть список доступных команд."
    await message.answer(s)

@cmd_router.message(Command('help'))
async def cmd_help(message: Message):
    s = "\t ℹ️ Команды для работы с ботом:\n\n" \
        "\t /price — Узнать последнюю цену и данные по валютной паре.\n" \
        "\t /order — Разместить ордер на указанную пару.\n" \
        "\t /close_position — Автоматически закрыть позицию при достижении 0,1% прибыли.\n" \
        "\t /cancel — Отменить все действия.\n\n" \
        "\t Если у вас есть вопросы, обращайтесь!"
    await message.answer(s)

@cmd_router.message(Command('cancel'))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Все действия отменены.")


@cmd_router.message(Command('price'))
async def cmd_price(message: Message, state: FSMContext):
    await state.set_state(Form.pair_choice)
    await message.answer("Выберите одну из этих пар:", reply_markup=make_pairs_buttons())


@cmd_router.message(StateFilter(Form.pair_choice))
async def send_information(message: Message, state: FSMContext):
    await state.set_state(Form.pair_choice)
    text = message.text.strip()
    print(text)

    pairs = get_pairs(text)

    if isinstance(pairs, pd.DataFrame):
        response_dict = pairs.to_dict(orient='records')[0]
        response_text = "\n".join([f"{key}: {value}" for key, value in response_dict.items()])
    else:
        response_text = pairs

    await message.reply(response_text)
    await state.clear()


@cmd_router.message(Command('order'))
async def take_order(message: Message, state: FSMContext):
    await state.set_state(Form.order_type)
    s = "Вы можете купить или продать в тестовом режиме.\n"
    s += "Выберите одно из следующих:"
    await message.answer(s, reply_markup=make_order_buttons())


@cmd_router.message(StateFilter(Form.order_type))
async def take_order_type(message: Message, state: FSMContext):
    global order_type
    order_type = message.text.strip()
    await state.set_state(Form.order_pair)
    await message.reply("Выберите валютную пару:", reply_markup=make_pairs_buttons())



@cmd_router.message(StateFilter(Form.order_pair))
async def take_pairs(message: Message, state: FSMContext):
    global pairs
    pairs = message.text.strip()
    await state.set_state(Form.order_price)
    await message.reply("Укажите цену для этого заказа:")


@cmd_router.message(StateFilter(Form.order_price))
async def verify_order(message: Message, state: FSMContext):
    try:
        price = float(message.text.strip())
        order = pair_order(order_type, pairs, price)
        if isinstance(order, str):
            await message.reply(order)
        else:
            await message.reply(f"Заказ успешно выполнен: {order}")

    except ValueError:
        await message.reply("Цена должна быть числом. Попробуйте снова.")
    except Exception as e:
        await message.reply(f"Произошла ошибка: {e}")

@cmd_router.message(Command('close_position'))
async def close_position_pairs(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in user_orders or not user_orders[user_id]:
        await message.reply("У вас нет открытых ордеров.")
        return

    await state.set_state(Form.close_position)

    orders = user_orders[user_id]
    order_list = '\n'.join([f"{i+1}. {order}" for i, order in enumerate(orders)])
    await message.reply(f"Ваши открытые ордера:\n{order_list}\nВыберите номер ордера для закрытия.")

@cmd_router.message(StateFilter(Form.close_position))
async def close_order(message: Message, state: FSMContext):
    try:
        order_number = int(message.text.strip()) - 1
        user_id = message.from_user.id

        if user_id not in user_orders or not user_orders[user_id]:
            await message.reply("У вас нет открытых ордеров.")
            return

        orders = user_orders[user_id]

        if 0 <= order_number < len(orders):
            order_to_close = orders.pop(order_number)
            await message.reply(f"Закрытие ордера: {order_to_close}")
            monitor_and_closing(order_to_close)
        else:
            await message.reply("Неверный номер ордера. Попробуйте снова.")

    except ValueError:
        await message.reply("Пожалуйста, введите корректный номер ордера.")
    except Exception as e:
        await message.reply(f"Произошла ошибка: {e}")