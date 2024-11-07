from config import BYBIT_API_KEY, BYBIT_API_SECRET
from pybit.unified_trading import HTTP
import pandas as pd
from time import sleep


session = HTTP(
    api_key=BYBIT_API_KEY,
    api_secret=BYBIT_API_SECRET,
    testnet=True
)


def get_pairs(pair):
    try:
        resp = session.get_tickers(category="spot", pairs=pair)['result']['list']
        symbols = []
        for element in resp:
            if pair == element['symbol']:
                data = {
                    "Valyuta juftligi": element['symbol'],
                    "Oxirgi narx": element['lastPrice'],
                    "Eng yuqori taklif narxi": element['bid1Price'],
                    "Eng past taklif narxi": element['ask1Price'],
                    "24 soat ichidagi narx o'zgarishi foizi": element['price24hPcnt'],
                    "24 soat ichidagi eng yuqori narx": element["highPrice24h"],
                    "24 soat ichidagi eng past narx": element["lowPrice24h"],
                    "24 soat ichidagi savdo hajmi": element['turnover24h'],
                    "24 soat ichidagi savdo hajmi (miqdor)": element['volume24h'],
                }
                symbols.append(data)
        return pd.DataFrame(symbols) if symbols else f"No data found for {pair}"

    except Exception as e:
        return f"There was an error fetching {pair}\nError: {e}"


def pair_order(order_type, pair, price):
    try:
       side = 'Buy' if order_type.lower() == 'buy' else 'Sell'
       resp = session.place_order(
           category='spot',
           symbol=pair,
           side=side,
           orderType='Limit',
           qty=0.0001,
           price=price,
           timeInForce='PostOnly',
           orderLinkid='spot-test-postonly',
           isLeverage=0,
           orderFilter='Order'
       )
       return resp
    except Exception as e:
       if 'Insufficient balance' in str(e) or 'ErrCode: 170131' in str(e):
           return "Balansingizda pul yetarli emas"
       else:
           return f"There was an error: {e}"


def monitor_and_closing(pair, user_id):
    try:
        while True:
            position_info = session.get_positions(category='spot', symbol=pair)
            if not position_info['result']:
                return f'Нет открытой позиции для {pair}.'
                break
            position = position_info['result'][0]
            entry_price = float(position['entryPrice'])
            current_price = float(position['lastPrice'])
            profit_percent = ((current_price - entry_price) / entry_price) * 100

            if profit_percent >= 0.1:
                close_response = session.cancel_order(symbol=pair)

                if close_response['ret_code'] == 0:
                    return f"{user_id} Позиция по {pair} закрыта с прибылью {profit_percent:.2f}%"
                else:
                    return f"{user_id} Ошибка при закрытии позиции: {close_response['ret_msg']}"
                break
        sleep(5)
    except Exception as e:
        return f"Произошла ошибка при мониторинге позиции: {e}"