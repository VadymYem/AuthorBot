# (c) Dan G. && AuthorChe
#  
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
#  https://www.gnu.org/licenses/agpl-3.0.html
import asyncio
import collections
import contextlib
import copy
import json
import logging
import os
import time

try:
    import redis
except ImportError as e:
    redis = None
    if "RAILWAY" in os.environ:
        raise e


import typing

from herokutl.errors.rpcerrorlist import ChannelsTooMuchError
from herokutl.tl.types import Message, User

from . import main, utils
from .pointers import (
    BaseSerializingMiddlewareDict,
    BaseSerializingMiddlewareList,
    NamedTupleMiddlewareDict,
    NamedTupleMiddlewareList,
    PointerDict,
    PointerList,
)
from .tl_cache import CustomTelegramClient
from .types import JSONSerializable

__all__ = [
    "Database",
    "PointerList",
    "PointerDict",
    "NamedTupleMiddlewareDict",
    "NamedTupleMiddlewareList",
    "BaseSerializingMiddlewareDict",
    "BaseSerializingMiddlewareList",
]

logger = logging.getLogger(__name__)


class NoAssetsChannel(Exception):
    """Raised when trying to read/store asset with no asset channel present"""


class Database(dict):
    def __init__(self, client: CustomTelegramClient):
        super().__init__()
        self._client: CustomTelegramClient = client
        self._next_revision_call: int = 0
        self._revisions: typing.List[dict] = []
        self._assets: int = None
        self._me: User = None
        self._redis: typing.Any = None
        self._saving_task: asyncio.Future = None

    def __repr__(self):
        return object.__repr__(self)

    def _redis_save_sync(self):
        with self._redis.pipeline() as pipe:
            pipe.set(
                str(self._client.tg_id),
                json.dumps(self, ensure_ascii=True),
            )
            pipe.execute()

    async def remote_force_save(self) -> bool:
        """Force save database to remote endpoint without waiting."""
        if not self._redis:
            return False

        try:
            await utils.run_sync(self._redis_save_sync)
        except Exception:
            logger.exception("Failed to publish database to Redis")
            return False

        logger.debug("Published db to Redis")
        return True

    async def _redis_save(self) -> bool:
        """Save database to Redis with debouncing."""
        if not self._redis:
            return False

        try:
            await asyncio.sleep(5)
            await utils.run_sync(self._redis_save_sync)
            logger.debug("Published db to Redis")
            return True
        except Exception:
            logger.exception("Failed to publish database to Redis")
            return False
        finally:
            self._saving_task = None

    async def redis_init(self) -> bool:
        """Initialize Redis. Local JSON remains the durable fallback."""
        redis_uri = os.environ.get("REDIS_URL") or main.get_config_key("redis_uri")
        if not redis_uri:
            return False

        if redis is None:
            logger.error("Redis is configured, but the redis package is not installed")
            return False

        try:
            client = redis.Redis.from_url(
                redis_uri,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            await utils.run_sync(client.ping)
        except Exception:
            logger.exception("Redis is unavailable; using local database")
            return False

        self._redis = client
        return True

    async def init(self):
        """Asynchronous initialization unit"""
        if os.environ.get("REDIS_URL") or main.get_config_key("redis_uri"):
            await self.redis_init()

        self._db_file = main.BASE_PATH / f"config-{self._client.tg_id}.json"
        self.read()

        try:
            self._assets, _ = await utils.asset_channel(
                self._client,
                "assets",
                "🌆 Your assets will be stored here",
                archive=True,
                avatar="https://raw.githubusercontent.com/VadymYem/AuthorBot/main/assets/bot_pfp.jpg",
            )
        except ChannelsTooMuchError:
            self._assets = None
            logger.error(
                "Can't find and/or create assets folder\n"
                "This may cause several consequences, such as:\n"
                "- Non working assets feature (e.g. notes)\n"
                "- This error will occur every restart\n\n"
                "You can solve this by leaving some channels/groups"
            )

    def read(self):
        """Read database, preferring Redis and falling back to local snapshots."""
        if self._redis:
            try:
                raw = self._redis.get(str(self._client.tg_id))
                if raw:
                    self.update(**json.loads(raw.decode()))
                    return
            except Exception:
                logger.exception("Error reading Redis database; falling back to disk")

        for path in (self._db_file, self._db_file.with_suffix(".json.bak")):
            try:
                self.update(**json.loads(path.read_text(encoding="utf-8")))
                return
            except json.decoder.JSONDecodeError:
                logger.warning("Database file %s is corrupted", path)
            except FileNotFoundError:
                continue
            except Exception:
                logger.exception("Database read failed for %s", path)

        logger.debug("No readable database snapshot found; starting with an empty database")

    def _save_local_atomic(self) -> bool:
        """Persist a complete local snapshot atomically."""
        tmp = self._db_file.with_suffix(".json.tmp")
        backup = self._db_file.with_suffix(".json.bak")
        try:
            payload = json.dumps(self, indent=4, ensure_ascii=False)
            with open(tmp, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            with contextlib.suppress(Exception):
                os.chmod(tmp, 0o600)
            if self._db_file.exists():
                with contextlib.suppress(Exception):
                    backup.write_bytes(self._db_file.read_bytes())
                    os.chmod(backup, 0o600)
            os.replace(tmp, self._db_file)
            with contextlib.suppress(Exception):
                os.chmod(self._db_file, 0o600)
            return True
        except Exception:
            logger.exception("Database save failed!")
            with contextlib.suppress(Exception):
                tmp.unlink()
            return False

    def process_db_autofix(self, db: dict) -> bool:
        if not utils.is_serializable(db):
            return False

        for key, value in db.copy().items():
            if not isinstance(key, (str, int)):
                logger.warning(
                    "DbAutoFix: Dropped key %s, because it is not string or int",
                    key,
                )
                continue

            if not isinstance(value, dict):
                # If value is not a dict (module values), drop it,
                # otherwise it may cause problems
                del db[key]
                logger.warning(
                    "DbAutoFix: Dropped key %s, because it is non-dict, but %s",
                    key,
                    type(value),
                )
                continue

            for subkey in list(value):
                if not isinstance(subkey, (str, int)):
                    del db[key][subkey]
                    logger.warning(
                        (
                            "DbAutoFix: Dropped subkey %s of db key %s, because it is"
                            " not string or int"
                        ),
                        subkey,
                        key,
                    )
                    continue

        return True

    def save(self) -> bool:
        """Save database"""
        if not self.process_db_autofix(self):
            try:
                rev = self._revisions.pop()
                while not self.process_db_autofix(rev):
                    rev = self._revisions.pop()
            except IndexError:
                raise RuntimeError(
                    "Can't find revision to restore broken database from "
                    "database is most likely broken and will lead to problems, "
                    "so its save is forbidden."
                )

            self.clear()
            self.update(**rev)

            raise RuntimeError(
                "Rewriting database to the last revision because new one destructed it"
            )

        if self._next_revision_call < time.time():
            self._revisions += [copy.deepcopy(dict(self))]
            self._next_revision_call = time.time() + 3

        while len(self._revisions) > 15:
            self._revisions.pop(0)

        local_saved = self._save_local_atomic()

        if self._redis and not self._saving_task:
            self._saving_task = asyncio.ensure_future(self._redis_save())

        return local_saved

    async def store_asset(self, message: Message) -> int:
        """
        Save assets
        returns asset_id as integer
        """
        if not self._assets:
            raise NoAssetsChannel("Tried to save asset to non-existing asset channel")

        return (
            (await self._client.send_message(self._assets, message)).id
            if isinstance(message, Message)
            else (
                await self._client.send_message(
                    self._assets,
                    file=message,
                    force_document=True,
                )
            ).id
        )

    async def fetch_asset(self, asset_id: int) -> typing.Optional[Message]:
        """Fetch previously saved asset by its asset_id"""
        if not self._assets:
            raise NoAssetsChannel(
                "Tried to fetch asset from non-existing asset channel"
            )

        asset = await self._client.get_messages(self._assets, ids=[asset_id])

        return asset[0] if asset else None

    def get(
        self,
        owner: str,
        key: str,
        default: typing.Optional[JSONSerializable] = None,
    ) -> JSONSerializable:
        """Get database key"""
        try:
            return self[owner][key]
        except KeyError:
            return default

    def set(self, owner: str, key: str, value: JSONSerializable) -> bool:
        """Set database key"""
        if not utils.is_serializable(owner):
            raise RuntimeError(
                "Attempted to write object to "
                f"{owner=} ({type(owner)=}) of database. It is not "
                "JSON-serializable key which will cause errors"
            )

        if not utils.is_serializable(key):
            raise RuntimeError(
                "Attempted to write object to "
                f"{key=} ({type(key)=}) of database. It is not "
                "JSON-serializable key which will cause errors"
            )

        if not utils.is_serializable(value):
            raise RuntimeError(
                "Attempted to write object of "
                f"{key=} ({type(value)=}) to database. It is not "
                "JSON-serializable value which will cause errors"
            )

        super().setdefault(owner, {})[key] = value
        return self.save()

    def pointer(
        self,
        owner: str,
        key: str,
        default: typing.Optional[JSONSerializable] = None,
        item_type: typing.Optional[typing.Any] = None,
    ) -> typing.Union[JSONSerializable, PointerList, PointerDict]:
        """Get a pointer to database key"""
        value = self.get(owner, key, default)
        mapping = {
            list: PointerList,
            dict: PointerDict,
            collections.abc.Hashable: lambda v: v,
        }

        pointer_constructor = next(
            (pointer for type_, pointer in mapping.items() if isinstance(value, type_)),
            None,
        )

        if (current_value := self.get(owner, key, None)) and type(
            current_value
        ) is not type(default):
            raise ValueError(
                f"Can't switch the type of pointer in database (current: {type(current_value)}, requested: {type(default)})"
            )

        if pointer_constructor is None:
            raise ValueError(
                f"Pointer for type {type(value).__name__} is not implemented"
            )

        if item_type is not None:
            if isinstance(value, list):
                for item in self.get(owner, key, default):
                    if not isinstance(item, dict):
                        raise ValueError(
                            "Item type can only be specified for dedicated keys and"
                            " can't be mixed with other ones"
                        )

                return NamedTupleMiddlewareList(
                    pointer_constructor(self, owner, key, default),
                    item_type,
                )
            if isinstance(value, dict):
                for item in self.get(owner, key, default).values():
                    if not isinstance(item, dict):
                        raise ValueError(
                            "Item type can only be specified for dedicated keys and"
                            " can't be mixed with other ones"
                        )

                return NamedTupleMiddlewareDict(
                    pointer_constructor(self, owner, key, default),
                    item_type,
                )

        return pointer_constructor(self, owner, key, default)
