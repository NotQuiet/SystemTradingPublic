import time
import urllib.parse
from Scripts.Managers.TelegramBotManager import TelegramBotManager


class RsiEnvelopeAlertManager:
    def __init__(self, transaction_manager, alert_window_seconds=300):
        self.transaction_manager = transaction_manager
        self.alert_window_seconds = alert_window_seconds
        self.last_rsi_signal = {}
        self.last_envelope_signal = {}

    async def record_rsi_signal(self, symbol, interval, signal_type, rsi_value, price):
        key = (symbol, interval)
        self.last_rsi_signal[key] = {
            'time': time.time(),
            'interval': interval,
            'signal_type': signal_type,
            'rsi_value': rsi_value,
            'price': price
        }
        await self.check_and_create_transaction(symbol, interval)

    async def record_envelope_signal(self, symbol, interval, signal_type, envelope_value, price):
        key = (symbol, interval)
        self.last_envelope_signal[key] = {
            'time': time.time(),
            'interval': interval,
            'signal_type': signal_type,
            'envelope_value': envelope_value,
            'price': price
        }
        await self.check_and_create_transaction(symbol, interval)

    async def check_and_create_transaction(self, symbol, interval):
        key = (symbol, interval)
        rsi_signal = self.last_rsi_signal.get(key)
        envelope_signal = self.last_envelope_signal.get(key)

        if rsi_signal and envelope_signal:
            if rsi_signal['signal_type'] == envelope_signal['signal_type']:
                if abs(rsi_signal['time'] - envelope_signal['time']) <= self.alert_window_seconds:
                    signal_color = "🟢" if rsi_signal['signal_type'] == 'upper' else "🔴"

                    price_formatted = "{:.8f}".format(rsi_signal['price'])

                    symbol_encoded = urllib.parse.quote(f"BINANCE:{symbol}")

                    # Формируем ссылку на TradingView
                    tradingview_link = f"https://www.tradingview.com/chart/?symbol={symbol_encoded}"

                    message = (
                        f"{signal_color} - 🟣🔵 Сигналы совпали для *{symbol}* на интервале *{interval}*.\n"
                        f"RSI: {rsi_signal['rsi_value']} ({rsi_signal['signal_type']})\n"
                        f"Envelope: {envelope_signal['envelope_value']} ({envelope_signal['signal_type']})\n"
                        f"Текущая цена: *{price_formatted}*\n"
                        f"[Открыть в TradingView]({tradingview_link})"
                    )
                    await self.send_telegram_message(message)

                    # Удаляем сигналы после обработки
                    del self.last_rsi_signal[key]
                    del self.last_envelope_signal[key]
                else:
                    print(
                        f"Сигналы для {symbol} не совпадают по времени: RSI={rsi_signal['time']}, Envelope={envelope_signal['time']}")
            else:
                print(
                    f"Сигналы для {symbol} не совпадают по типу (RSI: {rsi_signal['signal_type']}, Envelope: {envelope_signal['signal_type']})")

    async def send_telegram_message(self, message: str):
        bot_manager = TelegramBotManager()
        await bot_manager.send_message_to_prod_group(message)
