#    ╔╗╔┌─┐┬─┐┌─┐┬ ┬
#    ║║║├┤ ├┬┘│  └┬┘
#    ╝╚╝└─┘┴└─└─┘ ┴

# Code is licensed under CC-BY-NC-ND 4.0 unless otherwise specified.
# https://creativecommons.org/licenses/by-nc-nd/4.0/
# You CANNOT edit this file without direct permission from the author.
# You can redistribute this file without any changes.

# meta developer: @nercymods, lite version by @blazeftg / @wsinfo for termux users
# scope: hikka_min 1.6.2
# requires: pydub ffmpeg requests

import os
import logging
from hikkatl.tl.types import Message
from pydub import AudioSegment
import requests
import base64
from .. import loader, utils

@loader.tds
class WhisperMod(loader.Module):
    """Module for speech recognition using Hugging Face"""

    strings = {
        "name": "WhisperMod",
        "audio_not_found": (
            "<b><emoji document_id=5818678700274617758>👮‍♀️</emoji>Not found to"
            " recognize.</b>"
        ),
        "recognized": (
            "<b><emoji"
            " document_id=5821302890932736039>🗣</emojA:</b>\n{transcription}"

uthorBot
        ),
        "error": (
            "<b><emoji document_id=5980953710157632545>❌</emoji>Error occurred during"
            " transcription: {error}</b>"
        ),
        "recognition": (
            "<b><emoji document_id=5307937750828194743>🫥</emoji>Recognition...</b>"
        ),
        "downloading": "<b><emoji document_id=5310189005181036109>🐍</emoji>Downloading, wait</b>",
        "autowhisper_enabled": (
            "<b><emoji document_id=5307937750828194743>🫥</emoji>Auto-whisper enabled"
            " in this chat.</b>"
        ),
        "autowhisper_disabled": (
            "<b><emoji document_id=5307937750828194743>🫥</emoji>Auto-whisper disabled"
            " in this chat.</b>"
        ),
        "hf_instructions": (
            "<emoji document_id=5238154170174820439>👩‍🎓</emoji> <b>How to get hugging face api token:</b>\n"
            "<b>&gt; Open Hugging Face and sign in.</b> <emoji document_id=4904848288345228262>👤</emoji> <b>\n"
            "&gt; Go to Settings → Access Tokens: </b><a href=\"https://huggingface.co/settings/tokens\"><b>https://huggingface.co/settings/tokens</b></a><b>.</b> <emoji document_id=5222142557865128918>⚙️</emoji> <b>\n"
            "&gt; Click New Token.</b> <emoji document_id=5431757929940273672>➕</emoji> <b>\n"
            "&gt; Select permission: \"make calls to the serverless Inference API\".</b> <emoji document_id=5253952855185829086>⚙️</emoji> <b>\n"
            "&gt; Click Create Token.</b> <emoji document_id=5253652327734192243>➕</emoji> <b>\n"
            "&gt; Copy the token and paste it into the config.</b> <emoji document_id=4916036072560919511>✅</emoji>"
        ),
        "hf_token_missing": (
            "<b><emoji document_id=5980953710157632545>❌</emoji>Missing hugging face api token</b>"
            " (<code>.cfg whispermod</code>)"
        )
    }
    strings_ua = {
        "audio_not_found": (
            "<b><emoji document_id=5818678700274617758>👮‍♀️</emoji>Не знайдено, що"
            " розпізнавати.</b>"
        ),
        "recognized": (
            "<b><emoji"
            " document_id=5821302890932736039>🗣</emoji>AuthorBot:</b>\n{transcription}"
        ),
        "error": (
            "<b><emoji document_id=5980953710157632545>❌</emoji>Помилка при"
            " перекладанні: {error}</b>"
        ),
        "recognition": (
            "<b><emoji document_id=5307937750828194743>🫥</emoji>Розпізнаю...</b>"
        ),
        "downloading": (
            "<b><emoji document_id=5310189005181036109>🐍</emoji>Завантажую,"
            " зачекай...</b>"
        ),
        "autowhisper_enabled": (
            "<b><emoji document_id=5307937750828194743>🫥</emoji>Авторозпізнавання"
            " ввімкнено в цьому чаті.</b>"
        ),
        "autowhisper_disabled": (
            "<b><emoji document_id=5307937750828194743>🫥</emoji>Ну ладно.."
            " Не розпізнаю гс в чаті.</b>"
        ),
        "hf_instructions": (
            "<emoji document_id=5238154170174820439>👩‍🎓</emoji> <b>Як отримати api-токен hugging face:</b>\n"
            "<b>&gt; Відкрий Hugging Face і ввійди в аккаунт. </b><emoji document_id=4904848288345228262>👤</emoji><b>\n"
            "&gt; Перейди в Settings → Access Tokens: </b><a href=\"https://huggingface.co/settings/tokens\"><b>https://huggingface.co/settings/tokens</b></a><b>. </b><emoji document_id=5222142557865128918>⚙️</emoji><b>\n"
            "&gt; Натисни New Token. </b><emoji document_id=5431757929940273672>➕</emoji><b>\n"
            "&gt; Вибери дозволи: \"make calls to the serverless Inference API\". </b><emoji document_id=5253952855185829086>⚙️</emoji><b>\n"
            "&gt; Натисни Create Token. </b><emoji document_id=5253652327734192243>➕</emoji><b>\n"
            "&gt; Скопіюй токен і встав його в конфіг. </b><emoji document_id=4916036072560919511>✅</emoji>"
        ),
        "hf_token_missing": (
            "<b><emoji document_id=5980953710157632545>❌</emoji>Відсутній api-токен hugging face</b>"
            " (<code>.cfg whispermod</code>)"
        )
    }

    strings_ru = {
        "audio_not_found": (
            "<b><emoji document_id=5818678700274617758>👮‍♀️</emoji>Не найдено, что"
            " распознавать.</b>"
        ),
        "recognized": (
            "<b><emoji"
            " document_id=5821302890932736039>🗣</emoji>AuthorBot:</b>\n{transcription}"
        ),
        "error": (
            "<b><emoji document_id=5980953710157632545>❌</emoji>Ошибка при"
            " транскрипции: {error}</b>"
        ),
        "recognition": (
            "<b><emoji document_id=5307937750828194743>🫥</emoji>Распознавание...</b>"
        ),
        "downloading": (
            "<b><emoji document_id=5310189005181036109>🐍</emoji>Скачивание,"
            " подождите...</b>"
        ),
        "autowhisper_enabled": (
            "<b><emoji document_id=5307937750828194743>🫥</emoji>Автораспознавание"
            " включено в этом чате.</b>"
        ),
        "autowhisper_disabled": (
            "<b><emoji document_id=5307937750828194743>🫥</emoji>Автораспознавание"
            " отключено в этом чате.</b>"
        ),
        "hf_instructions": (
            "<emoji document_id=5238154170174820439>👩‍🎓</emoji> <b>Как получить api-токен hugging face:</b>\n"
            "<b>&gt; Откройте Hugging Face и войдите в аккаунт. </b><emoji document_id=4904848288345228262>👤</emoji><b>\n"
            "&gt; Перейдите в Settings → Access Tokens: </b><a href=\"https://huggingface.co/settings/tokens\"><b>https://huggingface.co/settings/tokens</b></a><b>. </b><emoji document_id=5222142557865128918>⚙️</emoji><b>\n"
            "&gt; Нажмите New Token. </b><emoji document_id=5431757929940273672>➕</emoji><b>\n"
            "&gt; Выберите разрешение: \"make calls to the serverless Inference API\". </b><emoji document_id=5253952855185829086>⚙️</emoji><b>\n"
            "&gt; Нажмите Create Token. </b><emoji document_id=5253652327734192243>➕</emoji><b>\n"
            "&gt; Скопируйте токен и вставьте его в конфиг. </b><emoji document_id=4916036072560919511>✅</emoji>"
        ),
        "hf_token_missing": (
            "<b><emoji document_id=5980953710157632545>❌</emoji>Отсутствует api-токен hugging face</b>"
            " (<code>.cfg whispermod</code>)"
        )
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "hf_api_key",
                None,
                lambda: "Hugging Face API Token (see .hfguide)",
                validator=loader.validators.Hidden(),
            ),
            loader.ConfigValue(
                "auto_voice",
                True,
                lambda: "Enable auto-recognition for voice messages",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "auto_video",
                True,
                lambda: "Enable auto-recognition for video messages",
                validator=loader.validators.Boolean()
            ),
        )

    async def _process_audio(self, file_path: str) -> str:
        """Process audio file and return transcription"""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_extension in ['.ogg', '.oga']:
                with open(file_path, "rb") as f:
                    audio_bytes = f.read()
            else:
                audio = AudioSegment.from_file(file_path, format=file_extension.lstrip('.'))
                audio.export("temp_audio.mp3", format="mp3")
                with open("temp_audio.mp3", "rb") as f:
                    audio_bytes = f.read()
                os.remove("temp_audio.mp3")

            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            response = await utils.run_sync(
                requests.post,
                url="https://api-inference.huggingface.co/models/openai/whisper-large-v3-turbo",
                headers={
                    "Authorization": f"Bearer {self.config['hf_api_key']}",
                    "x-use-cache": "false",
                    "x-wait-for-model": "true",
                    "Content-Type": "application/json"
                },
                json={"inputs": audio_b64},
            )

            if response.status_code != 200:
                error_msg = response.json().get('error', 'Unknown error')
                raise Exception(f"API Error ({response.status_code}): {error_msg}")

            return response.json()['text']
            
        except Exception as e:
            logging.exception("Audio processing error")
            raise e

    @loader.command(ru_doc="Распознать речь из голосового/видео сообщения в реплае")
    async def whisper(self, message: Message):
        """Transcribe speech from a voice/video message in reply"""
        if not self.config["hf_api_key"]:
            await utils.answer(message, self.strings["hf_token_missing"])
            return

        reply = await message.get_reply_message()
        if not reply or not reply.media:
            await utils.answer(message, self.strings["audio_not_found"])
            return

        download_msg = await utils.answer(message, self.strings["downloading"])
        try:
            file_path = await reply.download_media()
            await self.client.edit_message(
                message.chat_id,
                download_msg.id,
                self.strings["recognition"]
            )
            
            transcription = await self._process_audio(file_path)
            
            await self.client.edit_message(
                message.chat_id,
                download_msg.id,
                self.strings["recognized"].format(transcription=transcription)
            )
        except Exception as e:
            await self.client.edit_message(
                message.chat_id,
                download_msg.id,
                self.strings["error"].format(error=str(e))
            )
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

    @loader.command(ru_doc="Включить/выключить автораспознавание в этом чате")
    async def autowhspr(self, message: Message):
        """Toggle auto-transcription in current chat"""
        chat_id = str(message.chat_id)
        current_state = self.get("autowhspr", {})
        enabled = current_state.get(chat_id, False)

        if enabled:
            current_state.pop(chat_id, None)
            status_message = self.strings["autowhisper_disabled"]
        else:
            current_state[chat_id] = True
            status_message = self.strings["autowhisper_enabled"]
        self.set("autowhspr", current_state)
        await utils.answer(message, status_message)

    @loader.watcher(only_media=True)
    async def autowhisper_watcher(self, message: Message):
        """Auto-transcription watcher"""
        chat_id = str(message.chat_id)
        current_state = self.get("autowhspr", {})

        if current_state.get(chat_id, False):
            if (message.voice and self.config["auto_voice"]) or (message.video and self.config["auto_video"]):
                if not message.gif and not message.sticker and not message.photo:
                    try:
                        download_msg = await self.client.send_message(
                            message.chat_id,
                            self.strings["downloading"],
                            reply_to=message.id
                        )
                        
                        file_path = await message.download_media()
                        await self.client.edit_message(
                            message.chat_id,
                            download_msg.id,
                            self.strings["recognition"]
                        )
                        
                        transcription = await self._process_audio(file_path)
                        
                        await self.client.edit_message(
                            message.chat_id,
                            download_msg.id,
                            self.strings["recognized"].format(transcription=transcription)
                        )
                    except Exception as e:
                        await self.client.edit_message(
                            message.chat_id,
                            download_msg.id,
                            self.strings["error"].format(error=str(e))
                        )
                    finally:
                        if os.path.exists(file_path):
                            os.remove(file_path)

    @loader.command(ru_doc="Инструкция по получению токена Hugging Face")
    async def hfguide(self, message: Message):
        """Show Hugging Face token guide"""
        await utils.answer(message, self.strings['hf_instructions'])