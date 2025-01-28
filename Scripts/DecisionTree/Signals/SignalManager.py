import asyncio
import time
from Scripts.DecisionTree.Signals.SignalRepository import SignalRepository
from Scripts.Managers.TelegramBotManager import TelegramBotManager

class SignalManager:
    def __init__(self):
        self.signal_repository = SignalRepository()
        self.telegram_bot_manager = TelegramBotManager()
        self.patterns = self.load_patterns()
        self.last_alert_time = {}
        asyncio.create_task(self.periodic_clean_up())


    def load_patterns(self):
        # Определяем список паттернов с индивидуальным временем жизни (TTL)
        patterns = [
            {
                'name': 'RSI_Cross',
                'ttl': 180,
                'signals': [
                    {
                        'signal_type': 'RSI',
                        'condition': ['cross_up', 'cross_down'],
                        'intervals': ['1m', '5m', '15m'],
                        'ttl': 180
                    }
                ],
                'notification': {
                    'message': '👀 🔔 RSI {direction} для {symbol} на интервале {interval}.',
                    'env': 'dev',
                    'include_tradingview_link': True
                }
            },
            {
                'name': 'Envelope_Cross',
                'ttl': 180,
                'signals': [
                    {
                        'signal_type': 'Envelope',
                        'condition': ['cross_up', 'cross_down'],
                        'intervals': ['1m', '5m', '15m'],
                        'ttl': 180
                    }
                ],
                'notification': {
                    'message': '👀 📈 Конверт {direction} для {symbol} на интервале {interval}.',
                    'env': 'dev',
                    'include_tradingview_link': True
                }
            },
            {
                'name': 'MACD_Change',
                'ttl': 180,
                'signals': [
                    {
                        'signal_type': 'MACD',
                        'condition': ['change_up', 'change_down'],
                        'intervals': ['1m', '5m', '15m'],
                        'ttl': 180
                    }
                ],
                'notification': {
                    'message': '👀 📊 MACD {direction} для {symbol} на интервале {interval}.',
                    'env': 'dev',
                    'include_tradingview_link': True
                }
            },
            {
                'name': 'Pump_Dump',
                'ttl': 180,
                'signals': [
                    {
                        'signal_type': 'PumpDump',
                        'condition': ['pump', 'dump'],
                        'intervals': ['1m', '5m', '15m'],
                        'ttl': 180
                    }
                ],
                'notification': {
                    'message': '👀 🚀 Обнаружен {direction} для {symbol} на интервале {interval}.',
                    'env': 'prod',
                    'include_tradingview_link': True
                }
            },
            {
                'name': 'Open_Interest_Change',
                'ttl': 180,
                'signals': [
                    {
                        'signal_type': 'OpenInterest',
                        'condition': ['increase', 'decrease'],
                        'intervals': ['1m', '5m', '15m'],
                        'ttl': 180
                    }
                ],
                'notification': {
                    'message': '👀 🔔 Открытый интерес для {symbol} на интервале {interval} {direction} на {percentage_change:.2f}% за последние 3 периода.',
                    'env': 'prod',
                    'include_tradingview_link': True
                }
            },
            {
                'name': 'RSI_Envelope_Cross',
                'ttl': 300,
                'signals': [
                    {
                        'signal_type': 'RSI',
                        'condition': ['cross_up', 'cross_down'],
                        'intervals': ['1m', '5m', '15m'],
                        'ttl': 300
                    },
                    {
                        'signal_type': 'Envelope',
                        'condition': ['cross_up', 'cross_down'],
                        'intervals': ['1m', '5m', '15m'],
                        'ttl': 300
                    }
                ],
                'notification': {
                    'message': '👀 🔥 RSI и Конверт пересеклись для {symbol} на интервале {interval}.',
                    'env': 'prod',
                    'include_tradingview_link': True
                }
            },
            {
                'name': 'RSI_Envelope_MACD',
                'ttl': 300,
                'signals': [
                    {
                        'signal_type': 'RSI',
                        'condition': ['cross_up', 'cross_down'],
                        'intervals': ['15m', '5m'],
                        'ttl': 300
                    },
                    {
                        'signal_type': 'Envelope',
                        'condition': ['cross_up', 'cross_down'],
                        'intervals': ['15m', '5m'],
                        'ttl': 300
                    }
                ],
                'notification': {
                    'message': '{direction_emoji}{symbol} ({higher_interval}) {position}\nЦена: {price}\n🔵RSI: {rsi_value}\nОткрыть в CoinGlass (https://www.coinglass.com/tv/ru/Binance_{symbol})', #🟠MACD ({macd_m1_interval}){macd_m1_status} / ({macd_m5_interval}){macd_m5_status}\n
                    'env': 'breakdown',
                    'include_tradingview_link': False
                }
            }
        ]
        return patterns

    async def start_periodic_clean_up(self):
        asyncio.create_task(self.periodic_clean_up())

    async def periodic_clean_up(self):
        while True:
            await self.signal_repository.clean_up_signals()
            await asyncio.sleep(60)

    async def process_signal(self, symbol, interval, signal_type, signal_data):
        max_ttl = self.get_max_ttl_for_signal(signal_type)
        if max_ttl is None:
            max_ttl = 60

        await self.signal_repository.add_signal(symbol, interval, signal_type, signal_data, ttl=max_ttl)

        await self.check_patterns(symbol)

    def get_max_ttl_for_signal(self, signal_type):
        ttls = []
        for pattern in self.patterns:
            for req_signal in pattern['signals']:
                if req_signal['signal_type'] == signal_type:
                    ttls.append(req_signal.get('ttl', pattern.get('ttl', 60)))
        return max(ttls) if ttls else None

    async def check_patterns(self, symbol):
        current_time = time.time()

        for pattern in self.patterns:
            pattern_name = pattern['name']
            required_signals = pattern['signals']
            notification = pattern['notification']
            env = notification.get('env', 'prod')
            pattern_ttl = pattern.get('ttl', 60)

            pattern_matched = True
            message_params = {'symbol': symbol}
            signal_times = []
            collected_signals = {}

            for req_signal in required_signals:
                signal_type = req_signal['signal_type']
                conditions = req_signal.get('condition', [])
                intervals = req_signal.get('intervals', [])
                signal_found = False
                signal_ttl = req_signal.get('ttl', pattern_ttl)

                for interval in intervals:
                    signal = await self.signal_repository.get_signal(symbol, interval, signal_type)
                    if signal:
                        if signal['data'].get('direction') in conditions:
                            signal_age = current_time - signal['timestamp']
                            if signal_age <= signal_ttl:
                                signal_found = True
                                signal_times.append(signal['timestamp'])
                                collected_signals[(signal_type, interval)] = signal
                                message_params.update({
                                    'interval': interval,
                                    'direction': signal['data'].get('direction'),
                                    'direction_emoji': self.get_direction_emoji(signal_type, signal['data'].get('direction'))
                                })
                                break

                if not signal_found:
                    print(
                        f"DEBUG: Сигнал {signal_type} для {symbol} не найден или не соответствует условиям в интервалах {intervals}")
                    pattern_matched = False
                    break

            if pattern_matched:
                last_alert = self.last_alert_time.get((symbol, pattern_name), 0)
                time_since_last_alert = current_time - last_alert

                if pattern_name == 'RSI_Envelope_MACD':
                    rsi_signal = collected_signals.get(('RSI', '15m'))

                    rsi_direction = rsi_signal['data'].get('direction')
                    if rsi_direction == 'cross_up':
                        position = 'SHORT'
                        direction_emoji = '🔴'
                    else:
                        position = 'LONG'
                        direction_emoji = '🟢'

                    message_params.update({
                        'higher_interval': '15m',
                        'price': rsi_signal['data'].get('price', 'N/A') if rsi_signal else 'N/A',
                        'rsi_value': rsi_signal['data'].get('rsi_value', 'N/A') if rsi_signal else 'N/A',
                        'position': position,
                        'direction_emoji': direction_emoji
                    })

                    sent_alert_key = (symbol, pattern_name, 'sent_alerts')
                    sent_alerts = self.last_alert_time.get(sent_alert_key, [])
                    self.last_alert_time[sent_alert_key] = sent_alerts
                    self.last_alert_time[(symbol, pattern_name)] = current_time
                else:
                    if time_since_last_alert >= pattern_ttl:
                        await self.send_pattern_alert(symbol, pattern, message_params)
                        self.last_alert_time[(symbol, pattern_name)] = current_time

    def get_direction_emoji(self, signal_type, direction):
        if signal_type == 'RSI':
            if direction == 'cross_up':
                return '🔴'
            elif direction == 'cross_down':
                return '🟢'
        return ''

    def translate_direction(self, signal_type, direction):
        translations = {
            'OpenInterest': {
                'increase': 'увеличился 📈',
                'decrease': 'уменьшился 📉'
            },
            'PumpDump': {
                'increase': 'увеличился 📈',
                'decrease': 'уменьшился 📉'
            },
            'MACD': {
                'change_up': 'поменял направление вверх 📈',
                'change_down': 'поменял направление вниз 📉'
            },
            'RSI': {
                'cross_up': 'пересек верхнюю границу 📈',
                'cross_down': 'пересек нижнюю границу 📉'
            },
            'Envelope': {
                'cross_up': 'пересек верхнюю границу 📈',
                'cross_down': 'пересек нижнюю границу 📉'
            },
        }
        return translations.get(signal_type, {}).get(direction, direction)

    def get_higher_interval(self, required_signals, current_interval):
        intervals = [req['intervals'] for req in required_signals if req['intervals']]
        flat_intervals = [item for sublist in intervals for item in sublist]
        sorted_intervals = sorted(flat_intervals, key=lambda x: self.interval_to_seconds(x), reverse=True)
        for interval in sorted_intervals:
            if self.interval_to_seconds(interval) > self.interval_to_seconds(current_interval):
                return interval
        return current_interval

    def get_lower_interval(self, required_signals, current_interval):
        intervals = [req['intervals'] for req in required_signals if req['intervals']]
        flat_intervals = [item for sublist in intervals for item in sublist]
        sorted_intervals = sorted(flat_intervals, key=lambda x: self.interval_to_seconds(x))
        for interval in sorted_intervals:
            if self.interval_to_seconds(interval) < self.interval_to_seconds(current_interval):
                return interval
        return current_interval

    def interval_to_seconds(self, interval):
        mapping = {
            '1s': 1,
            '1m': 60,
            '3m': 180,
            '5m': 300,
            '15m': 900,
            '30m': 1800,
            '1h': 3600,
            '2h': 7200,
            '4h': 14400,
            '6h': 21600,
            '8h': 28800,
            '12h': 43200,
            '1d': 86400,
            '3d': 259200,
            '1w': 604800,
            '1M': 2592000,
        }
        return mapping.get(interval, 60)

    async def send_pattern_alert(self, symbol, pattern, message_params):
        notification = pattern['notification']
        message_template = notification['message']
        env = notification.get('env', 'prod')

        try:
            message = message_template.format(**message_params)
        except KeyError as e:
            print(
                f"ERROR: Ошибка форматирования сообщения: {e}. Message template: {message_template}, Params: {message_params}")
            return

        try:
            if env == 'prod':
                await self.telegram_bot_manager.send_message_to_prod_group(message)
            elif env == 'dev':
                await self.telegram_bot_manager.send_message_to_dev_group(message)
            elif env == 'breakdown':
                await self.telegram_bot_manager.send_message_to_breakdown_group(message)
            else:
                await self.telegram_bot_manager.send_message_to_prod_group(message)  # По умолчанию в прод

        except Exception as e:
            print(f"ERROR: Ошибка при отправке сообщения: {e}")

