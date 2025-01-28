from Scripts.Managers.TelegramBotManager import TelegramBotManager
import urllib.parse

class OpenInterestAlertManager:
    def __init__(self):
        self.telegram_bot_manager = TelegramBotManager()

    async def send_open_interest_alert(self, symbol, percentage_change, interval):
        symbol_encoded = urllib.parse.quote(f"BINANCE:{symbol}")
        tradingview_link = f"https://www.tradingview.com/chart/?symbol={symbol_encoded}"

        direction = "увеличился 📈" if percentage_change > 0 else "уменьшился 📉"
        message = (
            f"🔔 Открытый интерес для *{symbol}* на интервале *{interval}* {direction} на *{abs(percentage_change):.2f}%* за последние 3 периода.\n"
            f"[Открыть в TradingView]({tradingview_link})"
        )
        await self.telegram_bot_manager.send_message_to_prod_group(message)
        print(f"Отправлено уведомление об изменении открытого интереса для {symbol} на интервале {interval}.")
