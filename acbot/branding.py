"""Bundled AuthorBot artwork and Telegram photo helpers."""

from pathlib import Path

from aiogram.types import InputFile, InlineQueryResultCachedPhoto, InlineQueryResultPhoto

ASSETS = Path(__file__).resolve().parents[1] / "assets"
BOT_PHOTO = ASSETS / "bot_pfp.jpg"
AUTHOR_PHOTO = ASSETS / "acbot_pfp.jpg"
DEFAULT_BANNER = "authorbot:photo"
LEGACY_BANNERS = {
    "https://raw.githubusercontent.com/VadymYem/AuthorBot/main/assets/bot_pfp.jpg",
    "https://raw.githubusercontent.com/AuthorGramProject/AuthorBot/main/assets/bot_pfp.jpg",
}


def bot_photo() -> InputFile:
    """Create a fresh upload object; callers own its lifetime."""
    return InputFile(str(BOT_PHOTO))


def photo_result(photo: str, *, thumb: str = None, **kwargs):
    """Use cached Telegram photos without treating a file_id as a URL."""
    if photo.startswith(("https://", "http://")):
        return InlineQueryResultPhoto(photo_url=photo, thumb_url=thumb or photo, **kwargs)
    return InlineQueryResultCachedPhoto(photo_file_id=photo, **kwargs)
