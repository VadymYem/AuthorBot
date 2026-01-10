from .. import loader, utils
import aiohttp
import json
import asyncio

@loader.tds
class AIDevMod(loader.Module):
    """Module for interacting with AI (Gemini) for development purposes"""
    
    strings = {"name": "AIDev"}

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "api_key",
                "",
                lambda: "API Key for Gemini AI",
            ),
            loader.ConfigValue(
                "model",
                "gemini-3-flash-preview",
                lambda: "Model for AI requests",
            ),
        )

    async def aidevcmd(self, message):
        """<prompt> - Ask AI for assistance with code or files"""
        if not self.config["api_key"]:
            return await utils.answer(message, "<b>Error:</b> Please set your <code>api_key</code> in config!")

        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()
        
        # Security: Handle empty content
        prompt = args or ""
        context = ""

        if reply:
            if reply.text:
                context = reply.text
            
            # Properly handling files to avoid 'name file is not defined' error
            if reply.media:
                # We define 'file_data' locally and check its existence
                file_data = await message.client.download_media(reply.media, bytes)
                if file_data:
                    try:
                        context += f"\n\n[File Context]:\n{file_data.decode('utf-8', 'ignore')}"
                    except Exception:
                        context += "\n\n[Binary file attached]"

        full_prompt = f"{prompt}\n\n{context}".strip()
        
        if not full_prompt:
            return await utils.answer(message, "<b>Error:</b> Empty prompt. Provide text or reply to a message.")

        await utils.answer(message, "<b>AI is thinking...</b>")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.config['model']}:generateContent?key={self.config['api_key']}"
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}]
        }
        headers = {'Content-Type': 'application/json'}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=json.dumps(payload)) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        return await utils.answer(message, f"<b>API Error:</b> {resp.status}\n<code>{error_text}</code>")
                    
                    data = await resp.json()
                    # Safe access to response data
                    try:
                        ai_response = data['candidates'][0]['content']['parts'][0]['text']
                    except (KeyError, IndexError):
                        ai_response = "<b>Error:</b> Failed to parse AI response."

                    # Flood protection
                    await asyncio.sleep(0.3)
                    await utils.answer(message, ai_response)

        except Exception as e:
            await utils.answer(message, f"<b>Request failed:</b> <code>{str(e)}</code>")