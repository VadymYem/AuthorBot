from .. import loader, utils
import aiohttp

@loader.tds
class CurrencyMod(loader.Module):
    """Модуль для відстеження курсу валют (USD, EUR) та криптовалют (BTC, ETH)"""

    strings = {"name": "CurrencyMod"}

    async def ratecmd(self, message):
        """Показати актуальний курс валют до гривні та основної крипти"""
        await utils.answer(message, "⏳ <b>Отримую дані...</b>")

        try:
            async with aiohttp.ClientSession() as session:
                # Отримання курсу валют ПриватБанку
                async with session.get("https://api.privatbank.ua/p24api/pubinfo?json&exchange&coursid=5") as resp:
                    fiat_data = await resp.json()

                # Отримання курсу криптовалют з Binance
                async with session.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT") as resp:
                    btc_data = await resp.json()
                async with session.get("https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT") as resp:
                    eth_data = await resp.json()

            res_text = "<b>📊 Актуальний курс валют:</b>\n\n"

            # Обробка фіатних валют
            if isinstance(fiat_data, list):
                for coin in fiat_data:
                    if coin.get('ccy') in ['USD', 'EUR']:
                        buy = round(float(coin['buy']), 2)
                        sale = round(float(coin['sale']), 2)
                        res_text += f"💵 <b>{coin['ccy']}/UAH</b>\n"
                        res_text += f"┣ Купівля: <code>{buy}</code>\n"
                        res_text += f"┗ Продаж: <code>{sale}</code>\n\n"

            # Обробка криптовалют
            btc_price = round(float(btc_data['price']), 2)
            eth_price = round(float(eth_data['price']), 2)

            res_text += "<b>🚀 Криптовалюти (USDT):</b>\n"
            res_text += f"┣ <b>BTC:</b> <code>${btc_price:,}</code>\n"
            res_text += f"┗ <b>ETH:</b> <code>${eth_price:,}</code>"

            await utils.answer(message, res_text)

        except Exception as e:
            await utils.answer(message, f"❌ <b>Помилка при отриманні даних:</b>\n<code>{e}</code>")