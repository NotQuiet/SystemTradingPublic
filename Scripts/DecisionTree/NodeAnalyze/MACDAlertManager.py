from Scripts.Managers.TelegramBotManager import TelegramBotManager
import urllib.parse
class MACDAlertManager:
    def __init__(self, transaction_manager):
        self.transaction_manager = transaction_manager
        self.telegram_bot_manager = TelegramBotManager()

    async def send_telegram_message(self, message: str):
        await self.telegram_bot_manager.send_message_to_prod_group(message)

    async def process_interval_alert(self, tokenPair: str, direction: str, macd_value: float, signal_value: float, interval: str, price: float):
        price_formatted = "{:.8f}".format(price)
        symbol_encoded = urllib.parse.quote(f"BINANCE:{tokenPair}")

        # Формируем ссылку на TradingView
        tradingview_link = f"https://www.tradingview.com/chart/?symbol={symbol_encoded}"

        if direction == "cross_up":
            await self.handle_trade_signal(tokenPair, "long", price, interval)

        elif direction == "cross_down":
            await self.handle_trade_signal(tokenPair, "short", price, interval)

        else:
            message = (
                f"ℹ️ *{tokenPair}*: Получен сигнал MACD на таймфрейме *{interval}*.\n"
                f"Текущая цена: *{price_formatted}*\n"
                f"[Открыть в TradingView]({tradingview_link})"
            )


    async def handle_trade_signal(self, symbol, direction, price, interval):
        # Получаем активную сделку по символу и интервалу
        existing_transaction = self.transaction_manager.get_active_transaction_by_symbol_and_interval(symbol, interval)

        if existing_transaction:
            # Если уже есть открытая сделка
            if existing_transaction.direction != direction:
                # Если направление отличается, закрываем текущую сделку и открываем новую
                await self.transaction_manager.close_transaction(existing_transaction.id, price)
                await self.transaction_manager.create_transaction(symbol, price, direction, interval)
                print(f"Сделка по {symbol} закрыта и открыта новая в направлении {direction} на интервале {interval}.")
            else:
                # Если направление совпадает, ничего не делаем
                print(f"Сделка по {symbol} уже открыта в направлении {direction} на интервале {interval}.")
        else:
            # Если сделки нет, открываем новую
            await self.transaction_manager.create_transaction(symbol, price, direction, interval)
            print(f"Открыта новая сделка по {symbol} в направлении {direction} на интервале {interval}.")
