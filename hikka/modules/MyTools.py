from .. import loader, utils
from telethon.tl.types import Message

@loader.tds
class MyToolsMod(loader.Module):
    """Small tools for personal use"""
    strings = {"name": "MyTools"}

    async def idcmd(self, message: Message):
        """Show ID of user or chat"""
        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()
        
        if reply:
            user = await message.client.get_entity(reply.sender_id)
            chat = await message.client.get_entity(message.peer_id)
            text = f"👤 <b>User ID:</b> <code>{user.id}</code>\n"
            text += f"💬 <b>Chat ID:</b> <code>{chat.id}</code>"
        elif args:
            try:
                user = await message.client.get_entity(args)
                text = f"👤 <b>Entity ID:</b> <code>{user.id}</code>"
            except Exception:
                text = "❌ <b>Can't find this entity</b>"
        else:
            chat = await message.client.get_entity(message.peer_id)
            text = f"👤 <b>Your ID:</b> <code>{message.sender_id}</code>\n"
            text += f"💬 <b>Chat ID:</b> <code>{chat.id}</code>"
            
        await utils.answer(message, text)
