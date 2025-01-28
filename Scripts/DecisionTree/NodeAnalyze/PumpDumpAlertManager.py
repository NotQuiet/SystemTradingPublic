from Scripts.Managers.TelegramBotManager import TelegramBotManager
import urllib.parse

class PumpDumpAlertManager:
    def __init__(self, transaction_manager):
        self.transaction_manager = transaction_manager
        self.telegram_bot_manager = TelegramBotManager()

    async def send_telegram_message(self, message: str):
        await self.telegram_bot_manager.send_message_to_prod_group(message)

    async def process_pump_dump_alert(self, tokenPair: str, event_type: str, price_change: float, interval: str, price: float):
        price_formatted = "{:.8f}".format(price)
        price_change_formatted = "{:.2f}".format(price_change)

        symbol_encoded = urllib.parse.quote(f"BINANCE:{tokenPair}")

        # Формируем ссылку на TradingView
        tradingview_link = f"https://www.tradingview.com/chart/?symbol={symbol_encoded}"

        if event_type == "pump":
            message = (
                f"💹 *{tokenPair}* резкий рост цены!\n"
                f"Цена выросла на *{price_change_formatted}%* по сравнению со средним значением последних 5 свечей на таймфрейме *{interval}*.\n"
                f"Текущая цена: *{price_formatted}*\n"
                f"[Открыть в TradingView]({tradingview_link})"
            )
        elif event_type == "dump":
            message = (
                f"📉 *{tokenPair}* резкое падение цены!\n"
                f"Цена упала на *{price_change_formatted}%* по сравнению со средним значением последних 5 свечей на таймфрейме *{interval}*.\n"
                f"Текущая цена: *{price_formatted}*\n"
                f"[Открыть в TradingView]({tradingview_link})"
            )
        else:
            message = (
                f"ℹ️ *{tokenPair}*: Обнаружено значительное изменение цены на таймфрейме *{interval}*.\n"
                f"Изменение цены: *{price_change_formatted}%*\n"
                f"Текущая цена: *{price_formatted}*\n"
                f"[Открыть в TradingView]({tradingview_link})"
            )

        await self.send_telegram_message(message)
