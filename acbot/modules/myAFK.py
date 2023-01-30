__version__ = (2, 0, 0)
#                         © Copyright 2023                             
#                                                                        
#                https://t.me/Den4ikSuperOstryyPer4ik                    
#                              and                                       
#                      https://t.me/ToXicUse                             
#                                                                         
#                 🔒 Licensed under the GNU AGPLv3                       
#             https://www.gnu.org/licenses/agpl-3.0.html                 
#                   

import time
import logging
import datetime
from telethon import types
from .. import loader, utils
from ..inline.types import InlineCall
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.account import UpdateProfileRequest

logger = logging.getLogger(__name__)


class MyAfkMod(loader.Module):
	"""Custom AFK module by AstroModules"""

	async def client_ready(self, client, db):
		self._db = db
		self._me = await client.get_me()

	strings = {
		"name": "myAFK",

		"lname": "| afk.",
		"lname0": " ",

		"bt_off_afk": "⚠️ АФК режим вимкнено",
		"bt_on_afk": "💤 АФК режим знову активний",

		"_cfg_cst_btn": "Посилання на чат, яке перебуватиме під текстом АФК. Щоб зовсім прибрати, напишіть None",
		"feedback_bot__text": "Username вашого feedback бота. Якщо немає - не чіпайте",
		"button__text": "Додати інлайн кнопку відключення режиму АФК?",
		"custom_text__afk_text": "Кастомний текст афк. Використовуй {time} для виведення останнього часу перебування у мережі",
	}

	def render_settings(self):
		active = self._db.get(__name__, 'afk')
		if active == True:
			a_active = "Ввімкнено✅"
		else:
			a_active = 'Вимкнено 🚫'
		change_bio = self._db.get(__name__, 'change_bio')
		if change_bio == True:
			a_change_bio = 'Так'
		else:
			a_change_bio = 'Ні'
		change_name = self._db.get(__name__, 'change_name')
		if change_name == True:
			a_change_name = 'Так'
		else:
			a_change_name = 'Ні'
		fb = self.config['feedback_bot']
		text = (
			f'🥷🏼 <b>myAFK</b>\n'
			f'├<b>{a_active}</b>\n'
			f'<b>├Зміна біографії:</b> <code>{a_change_bio}</code> 📖\n'
			f'<b>├Зміна префікса:</b> <code>{a_change_name}</code> 📝\n'
			f'<b>└Бот для зв`язку:</b> <code>@{fb}</code> 🤖'
		)
		return text


	def __init__(self):
		self.config = loader.ModuleConfig(
			loader.ConfigValue(
				"prefix",
				'| afk.',
				doc=lambda: 'Префікс, який додаватиметься до вашого імені під час входу до АФК'
			),
			loader.ConfigValue(
				"feedback_bot",
				None,
				doc=lambda: self.strings("feedback_bot__text"),
			),
			loader.ConfigValue(
				"custom_text__afk",
				"None",
				doc=lambda: self.strings("custom_text__afk_text"),
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
				lambda: "Чати, в яких AFК не спрацьовуватиме",
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

	@loader.command()
	async def afkconfig(self, message):
		"""- відкрити налаштування модуля"""
		
		await self.inline.form(message=message, text='<b>⚙️ Открыть настройки</b>', reply_markup=[{'text': '🔴 Открыть', 'callback': self.settings}])

	@loader.command()
	async def afk(self, message):
		"""- увійти до АФК режиму"""
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
		change_bio = self._db.get(__name__, "change_bio")
		change_name = self._db.get(__name__, "change_name")

		try:
			ls = user.full_user.last_name
		except:
			ls = ''
		about = user.full_user.about

		self._db.set(__name__, 'about', about)
		self._db.set(__name__, "ln", ls)

		if change_name == False and change_bio == False:
			await utils.answer(message, '<emoji document_id=5188391205909569136>✅</emoji> <b>АФК</b> режим успішно <b>ввімкнено</b>!')
			return

		if change_name == True:
			prefix = self.config['prefix']
			last_name = f'{ls} {prefix}'
			await message.client(UpdateProfileRequest(last_name=last_name))

		if change_bio == True:
			if self.config['feedback_bot'] == None:
				await message.client(UpdateProfileRequest(about='I`m offline', last_name=self.config['prefix']))
			else:
				a_afk_bio = 'Нема на місці, перебуваю в афк. Зв`язок тільки через: '
				feedback = self.config['feedback_bot']
				await message.client(UpdateProfileRequest(about=f'{a_afk_bio} {feedback}'))

		await utils.answer(message, '<emoji document_id=5188391205909569136>✅</emoji> <b>АФК</b> режим успішно <b>ввімкнено</b>!')
		

	@loader.command()
	async def unafk(self, message):
		"""- вийти з режиму АФК"""

		self._db.set(__name__, "afk", False)
		self._db.set(__name__, "gone", None)
		self._db.set(__name__, "ratelimit", [])
		change_bio = self._db.get(__name__, "change_bio")
		change_name = self._db.get(__name__, "change_name")

		if change_name == False and change_bio == False:
			await utils.answer(message, '<emoji document_id=5465665476971471368>❌</emoji> <b>АФК</b> режим успішно <b>вимкнено</b>!')
			return

		if change_name == True:
			ls = self._db.get(__name__, 'ln')
			await message.client(UpdateProfileRequest(last_name=ls))

		if change_bio == True:
			try:
				await message.client(UpdateProfileRequest(about=f'{self.db.get(__name__, "about")}'))
			except:
				await message.client(UpdateProfileRequest(about="@AuthorChe - poems from the heart ❤️."))
		await utils.answer(message, '<emoji document_id=5465665476971471368>❌</emoji> <b>АФК</b> режим успішно <b>вимкнено</b>!')
		await self.allmodules.log("myAFK now stoped.")


	@loader.watcher()
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
		change_bio = self._db.get(__name__, "change_bio")
		change_name = self._db.get(__name__, "change_name")
		self._db.set(__name__, 'about', about)
		self._db.set(__name__, "ln", ls)
		await self.allmodules.log("myAFК now not working.")

		if change_name == False and change_bio == False:
			await call.edit(self.strings["bt_off_afk"])
			return

		if change_name == True:
			ls = self._db.get(__name__, 'ln')
			await message.client(UpdateProfileRequest(last_name=ls))

		if change_bio == True:
			try:
				await self._client(UpdateProfileRequest(about=f'{self.db.get(__name__, "about")}'))
			except:
				await self._.client(UpdateProfileRequest(about="@AuthorChe - poems from the heart ❤️."))

		await call.edit(self.strings["bt_off_afk"])

	async def settings(self, call: InlineCall):
		info = self.render_settings()
		await call.edit(
			text=info,
			reply_markup=[
				[
					{
						'text': "📖 біографія",
						'callback': self.settings_about
					},
					{
						'text': '📝 Префікс',
						'callback': self.settings_name
					}
				],
				[
					{
						"text": "🚫 Закрити",
						"action": 'close'
					}
				]
			]
		)

	async def settings_name(self, call: InlineCall):
		await call.edit(
			text=(
				f'<b>📖 Встановлення префіксa</b>\n\n'
				+ '<i>❔ Чи хотіли б Ви, щоб при вході в АФК режим до вашого '
				+ 'ніку додавався префікс <code>| afk.</code> ?</i>\n\n'
				+ 'ℹ️ Також Ви можете <b>змінити префікс</b>, '
				+ '<b>скасувати</b> або <b>здійснити</b> дію, натиснувши <b>кнопки нижче</b>'
),
			reply_markup=[
				[
					{
						'text': '✅ Tак',
						"callback": self.name_yes
					},
					{
						"text": '🚫 Ні',
						"callback": self.name_no
					}
				],
				[{'text': '↩️ Назад', 'callback': self.settings}]
			]
		)
	async def name_yes(self, call: InlineCall):
		self._db.set(__name__, 'change_name', True)
		info = self.render_settings()
		await call.edit(
			text=info,
			reply_markup=[
				[
					{
						'text': "📖 біографія",
						'callback': self.settings_about
					},
					{
						'text': '📝 Префікс',
						'callback': self.settings_name
					}
				],
				[
					{
						"text": "🚫 Закрити",
						"action": 'close'
					}
				]
			]
		)
	async def name_no(self, call: InlineCall):
		self._db.set(__name__, 'change_name', False)
		info = self.render_settings()
		await call.edit(
			text=info,
			reply_markup=[
				[
					{
						'text': "📖 біографія",
						'callback': self.settings_about
					},
					{
						'text': '📝 Префікс',
						'callback': self.settings_name
					}
				],
				[
					{
						"text": "🚫 Закрити",
						"action": 'close'
					}
				]
			]
		)
	async def settings_about(self, call: InlineCall):
		if self.config['feedback_bot'] == None:
			text = (
				f'📖 <b>Зміна біографії</b>'
+ '\n\n❔ <b>Хочете</b> Чи Ви, щоб при <b>вході в АФК</b> режим Ваша біографія <b>змінювалася</b>'
				+ '  на "<code>Знаходжуся в афк</code>"?\n\n'
+ 'ℹ️ Так само Ви можете <b>змінити біографію</b> у <b>конфізі</b>. '
				+ 'Можна <b>скасувати</b> або <b>здійснити</b> дію, натиснувши <b>кнопку нижче</b>'
			)
		else:
			text = (
				f'📖 <b>Зміна біографії</b>'
+ '\n\n❔ <b>Чи бажаєте</b> Ви, щоб при <b>вході в АФК</b> режим '
				+ 'Ваша біографія <b>змінювалася</b> на "<code>Немає, на місці знаходжуся в афк</code><code>.'
				+ f' Зв`язок тільки через @{self.config["feedback_bot"]}</code>"?\n🤖 <b>Бот для зв`язку</b>: <code>@{self.config["feedback_bot"]}</code>\n\n'
				+ 'ℹ️ Також Ви можете <b>змінити біографію</b> в <b>конфізі</b>. '
				+ 'Можна <b>скасувати</b> або <b>здійснити</b> дію, натиснувши <b>кнопки нижче</b>'
			)
		await call.edit(
			text=text,
			reply_markup=[
				[
					{
						'text': '✅ Так',
						"callback": self.bio
					},
					{
						"text": '🚫 Ні',
						"callback": self.bio_n
					}
				],
				[{'text': '↩️ Назад', 'callback': self.settings}]
			]
		)
	async def bio(self, call: InlineCall):
		self._db.set(__name__, 'change_bio', True)
		info = self.render_settings()
		await call.edit(
			text=info,
			reply_markup=[
				[
					{
						'text': "📖 біографія",
						'callback': self.settings_about
					},
					{
						'text': '📝 Префікс',
						'callback': self.settings_name
					}
				],
				[
					{
						"text": "🚫 Закрити",
						"action": 'close'
					}
				]
			]
		)
	async def bio_n(self, call: InlineCall):
		self._db.set(__name__, 'change_bio', False)
		info = self.render_settings()
		await call.edit(
			text=info,
			reply_markup=[
				[
					{
						'text': "📖 біографія",
						'callback': self.settings_about
					},
					{
						'text': '📝 Префікс',
						'callback': self.settings_name
					}
				],
				[
					{
						"text": "🚫 Закрити",
						"action": 'close'
					}
				]
			]
		)

	def get_afk(self):
		return self._db.get(__name__, "afk", False)