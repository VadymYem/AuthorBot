#                         © Copyright 2022                               
#                                                                        
#                https://t.me/Den4ikSuperOstryyPer4ik                    
#                              and                                       
#                      https://t.me/ToXicUse                             
#                                                                         
#                 🔒 Licensed under the GNU AGPLv3                       
#             https://www.gnu.org/licenses/agpl-3.0.html                 
#                                                                                                                 
# scope: inline

from .. import loader, utils

import logging
import datetime
import time

from telethon import types

from ..inline.types import InlineCall
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.account import UpdateProfileRequest

logger = logging.getLogger(__name__)


@loader.tds
class TxAFKMod(loader.Module):
	"""Афк модуль от AstroModules с изменением био и имени"""

	async def client_ready(self, client, db):
		self._db = db
		self._me = await client.get_me()

	strings = {
		"name": "myAFK",

		"lname": "| afk.",
		"lname0": " ",

		"bt_off_afk": "⚠️ АФК вимкнено",
		"bt_on_afk": "💤 АФК ввімкнено",

		"_cfg_cst_btn": "Посилання на чат, яке буде відображатися разом з повідомленням. (Щоб взагалі прибрати, напишіть None)",
		"standart_bio_text": "Кастомний опис профілю",
		"feedback_bot__text": "Юзер вашого фідбек бота (якщо є)",
		"button__text": "Додати інлайн кнопку відключення режиму АФК?",
		"custom_text__afk_text": "Кастомний текст афк. Використовуй {time} для виведення останнього часу перебування у мережі",
	}

	def __init__(self):
		self.config = loader.ModuleConfig(
			loader.ConfigValue(
				"feedback_bot",
				"None",
				doc=lambda: self.strings("feedback_bot__text"),
			),
			loader.ConfigValue(
				"custom_text__afk",
				"None",
				doc=lambda: self.strings("custom_text__afk_text"),
			),
			loader.ConfigValue(
				"standart_bio",
				"None",
				doc=lambda: self.strings("standart_bio_text"),
			),
			loader.ConfigValue(
				"custom_button",
				[
					"AuthorChe`s✍️",
					"https://t.me/AuthorChe",
				],
				lambda: self.strings("_cfg_cst_btn"),
				validator=loader.validators.Union(
					loader.validators.Series(fixed_len=2),
					loader.validators.NoneType(),
				),
			),
			loader.ConfigValue(
				"ignore_chats",
				[],
				lambda: "Чати, в яких при згадці AFК не спрацьовуватиме",
				validator=loader.validators.Series(
                    validator=loader.validators.Union(
                        loader.validators.TelegramID(),
                        loader.validators.RegExp("[0-9]"),
                    ),
                ),
			),
			loader.ConfigValue(
				"button",
				True,
				doc=lambda: self.strings("button__text"),
				validator=loader.validators.Boolean(),
			)

		)


	async def afkconfigcmd(self, message):
		"""- відкрити конфіг модуля"""
		await self.allmodules.commands["config"](
					await utils.answer(message, f"{self.get_prefix()}config myAFK")
				)

	async def afkcmd(self, message):
		"""- AFK режим"""
		try:
			user_id = (
				(
					(
						await self._client.get_entity(
							args if not args.isdigit() else int(args)
						)
					).id
				)
				if args
				else reply.sender_id
			)
		except Exception:
			user_id = self._tg_id

		user = await self._client(GetFullUserRequest(user_id))
		
		self._db.set(__name__, "afk", True)
		self._db.set(__name__, "gone", time.time())
		self._db.set(__name__, "ratelimit", [])
		a_afk_bio_nofb = "В афк."
		lastname = self.strings("lname")
		if self.config['feedback_bot'] == None:
			await message.client(UpdateProfileRequest(about=a_afk_bio_nofb, last_name=lastname))
		else:
			a_afk_bio = 'В даний момент я не в мережі. Зачекайте або зверніться через '
			feedback = self.config['feedback_bot']
			aaa = a_afk_bio + feedback
			await message.client(UpdateProfileRequest(about=aaa))
		await self.allmodules.log("goafk")
		await utils.answer(message, '<emoji document_id=5215519585150706301>👍</emoji> <b>АФК режим ввіменено!</b>')
		await message.client(UpdateProfileRequest(last_name=lastname))

	async def unafkcmd(self, message):
		"""- вийти з режиму AFK"""
		msg = await utils.answer(message, '<emoji document_id=5213107179329953547>⏰</emoji> <b>Вимикаю режим АФК...</b>')
		sbio = self.config['standart_bio']
		lastname0 = self.strings('lname0')
		self._db.set(__name__, "afk", False)
		self._db.set(__name__, "gone", None)
		self._db.set(__name__, "ratelimit", [])
		await self.allmodules.log("unafk")
		if sbio == None:
			await message.client(UpdateProfileRequest(about='', last_name=lastname0))
		else:
			await message.client(UpdateProfileRequest(about=sbio, last_name=lastname0))
		time.sleep(1)
		await utils.answer(msg, '<emoji document_id=5220108512893344933>🆘</emoji> <b>Режим AFK вимкнено!</b>')


	def _afk_custom_text(self) -> str:
		now = datetime.datetime.now().replace(microsecond=0)
		gone = datetime.datetime.fromtimestamp(
			self._db.get(__name__, "gone")
		).replace(microsecond=0)

		time = now - gone

		return (
			"<b> </b>\n"
			+ self.config["custom_text__afk"].format(
				time=time,
			)
		)


	async def watcher(self, message):
		if not isinstance(message, types.Message):
			return
		if utils.get_chat_id(message) in self.config['ignore_chats']: 
			return
		if message.mentioned or getattr(message.to_id, "user_id", None) == self._me.id:
			afk_state = self.get_afk()
			if not afk_state:
				return
			logger.debug("tagged!")
			ratelimit = self._db.get(__name__, "ratelimit", [])
			if utils.get_chat_id(message) in ratelimit:
				return
			else:
				self._db.setdefault(__name__, {}).setdefault("ratelimit", []).append(
					utils.get_chat_id(message)
				)
				self._db.save()
			user = await utils.get_user(message)
			if user.is_self or user.bot or user.verified:
				logger.debug("User is self, bot or verified.")
				return
			if self.get_afk() is False:
				return
			now = datetime.datetime.now().replace(microsecond=0)
			gone = datetime.datetime.fromtimestamp(
				self._db.get(__name__, "gone")
			).replace(microsecond=0)
			time = now - gone
			if self.config['custom_button'] == None:
				if self.config["button"] == False:
					if self.config["custom_text__afk"] == None:
						await self.inline.form(message=message, text=f"<b>🔅 Я зараз перебуваю в offline (не в мережі).\nВідповім пізніше</b>\n\nВостаннє був у мережі <code>{time}</code> тому.\n\n<i>Поки чекаєте, раджу переглянути пару творів в:</i>")
					else:
						await self.inline.form(message=message, text=self._afk_custom_text())
				
				elif self.config['button'] == True:
					if self.config["custom_text__afk"] == None:
						await self.inline.form(
							message=message, 
							text=f"<b>🔅 Я зараз перебуваю в offline (не в мережі).\nВідповім пізніше</b>\n\nВостаннє був у мережі <code>{time}</code> тому.\n\n<i>Поки чекаєте, раджу переглянути пару творів в:</i>", 
							reply_markup=[
								[
									{
										"text": "🚫 Вийти з афк 🚫", 
										"callback": self.button_cancel,
									}
								]
							]
						)

					else:
						await self.inline.form(
							message=message, 
							text=self._afk_custom_text(), 
							reply_markup=[
								[
									{
										"text": "🚫 Вийти з афк 🚫", 
										"callback": self.button_cancel,
									}
								]
							]
						)
			else:
				if self.config["button"] == False:
					if self.config["custom_text__afk"] == None:
						await self.inline.form(message=message, text=f"<b>🔅 Я зараз перебуваю в offline (не в мережі).\nВідповім пізніше</b>\n\nВостаннє був у мережі <code>{time}</code> тому.\n\n<i>Поки чекаєте, раджу переглянути пару творів в:</i>", reply_markup=[{"text": self.config['custom_button'][0], "url": self.config['custom_button'][1]}])
					else:
						await self.inline.form(message=message, text=self._afk_custom_text(), reply_markup=[{"text": self.config['custom_button'][0], "url": self.config['custom_button'][1]}])
				
				elif self.config['button'] == True:
					if self.config["custom_text__afk"] == None:
						await self.inline.form(
							message=message, 
							text=f"<b>🔅 Я зараз перебуваю в offline (не в мережі).\nВідповім пізніше</b>\n\nВостаннє був у мережі <code>{time}</code> тому.\n\n<i>Поки чекаєте, раджу переглянути пару творів в:</i>", 
							reply_markup=[
								[
									{
										"text": self.config['custom_button'][0],
										"url": self.config['custom_button'][1],
									}
								],
								[
									{
										"text": "🚫 Вийти з афк 🚫", 
										"callback": self.button_cancel,
									}
								]
							]
						)

					else:
						await self.inline.form(
							message=message, 
							text=self._afk_custom_text(), 
							reply_markup=[
								[
									{
										"text": self.config['custom_button'][0],
										"url": self.config['custom_button'][1],
									}
								],
								[
									{
										"text": "🚫 Вийти з афк 🚫", 
										"callback": self.button_cancel,
									}
								]
							]
						)

	async def button_cancel(self, call: InlineCall):
		self._db.set(__name__, "afk", False)
		self._db.set(__name__, "gone", None)
		self._db.set(__name__, "ratelimit", [])
		await self.allmodules.log("unafk")
		if self.config['standart_bio'] == None:
			lastname = self.strings("lname0")
			about = self.strings("lname0")
			await self._client(UpdateProfileRequest(about=about, last_name=lastname))
		else:
			aboutt = self.config['standart_bio']
			lastname = self.strings("lname0")
			await self._client(UpdateProfileRequest(about=aboutt, last_name=lastname))
		await call.edit(
		self.strings["bt_off_afk"],
		reply_markup=[
			{
				"text": "🔰 Ввійти в афк 🔰",
				"callback": self.button_cancel_on,
			}
		]
	)

	async def button_cancel_on(self, call: InlineCall):
		self._db.set(__name__, "afk", True)
		self._db.set(__name__, "gone", time.time())
		self._db.set(__name__, "ratelimit", [])
		a_afk_bio_nofb = "В афк."
		lastname = self.strings("lname")
		if self.config['feedback_bot'] == None:
			await self._client(UpdateProfileRequest(about=a_afk_bio_nofb, last_name=lastname))
		else:
			a_afk_bio = 'На даний момент в АФК. Зв`язок тільки через '
			feedback = self.config['feedback_bot']
			aaa = a_afk_bio + feedback
			await self._client(UpdateProfileRequest(about=aaa))
		await call.edit(
		self.strings["bt_on_afk"],
		reply_markup=[
			{
				"text": "🚫 Вийти з афк 🚫",
				"callback": self.button_cancel,
			}
		]
	)

	def get_afk(self):
		return self._db.get(__name__, "afk", False)
