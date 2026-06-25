import json
from collections.abc import Mapping
from typing import Any

import aiosqlite
from aiogram.fsm.storage.base import BaseStorage, StateType, StorageKey


class SqliteFSMStorage(BaseStorage):
    """
    A persistent FSM storage backed by SQLite.
    This prevents aiogram FSM state loss when the bot crashes or restarts.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._db_initialized = False

    async def _execute(self, query: str, params: tuple[Any, ...] = ()) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(query, params)
            await db.commit()

    async def _fetch_one(self, query: str, params: tuple[Any, ...] = ()) -> aiosqlite.Row | None:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                return await cursor.fetchone()

    async def _init_db(self) -> None:
        if self._db_initialized:
            return

        query = """
        CREATE TABLE IF NOT EXISTS fsm_state (
            chat_id INTEGER,
            user_id INTEGER,
            bot_id INTEGER,
            destiny TEXT,
            state TEXT,
            data TEXT,
            PRIMARY KEY (chat_id, user_id, bot_id, destiny)
        )
        """
        await self._execute(query)
        self._db_initialized = True

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        await self._init_db()
        state_str = getattr(state, "state", state) if state is not None else None

        row = await self._fetch_one(
            "SELECT data FROM fsm_state WHERE chat_id=? AND user_id=? AND bot_id=? AND destiny=?",
            (key.chat_id, key.user_id, key.bot_id, key.destiny),
        )

        data = row["data"] if row else "{}"

        if state_str is None and data == "{}":
            # Clean up if both state and data are empty
            await self._execute(
                "DELETE FROM fsm_state WHERE chat_id=? AND user_id=? AND bot_id=? AND destiny=?",
                (key.chat_id, key.user_id, key.bot_id, key.destiny),
            )
            return

        await self._execute(
            """
            INSERT INTO fsm_state (chat_id, user_id, bot_id, destiny, state, data)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(chat_id, user_id, bot_id, destiny) DO UPDATE SET state=excluded.state
            """,
            (key.chat_id, key.user_id, key.bot_id, key.destiny, state_str, data),
        )

    async def get_state(self, key: StorageKey) -> str | None:
        await self._init_db()
        row = await self._fetch_one(
            "SELECT state FROM fsm_state WHERE chat_id=? AND user_id=? AND bot_id=? AND destiny=?",
            (key.chat_id, key.user_id, key.bot_id, key.destiny),
        )
        return row["state"] if row else None

    async def set_data(self, key: StorageKey, data: Mapping[str, Any]) -> None:
        await self._init_db()
        data_str = json.dumps(data)

        row = await self._fetch_one(
            "SELECT state FROM fsm_state WHERE chat_id=? AND user_id=? AND bot_id=? AND destiny=?",
            (key.chat_id, key.user_id, key.bot_id, key.destiny),
        )
        state_str = row["state"] if row else None

        if state_str is None and data_str == "{}":
            await self._execute(
                "DELETE FROM fsm_state WHERE chat_id=? AND user_id=? AND bot_id=? AND destiny=?",
                (key.chat_id, key.user_id, key.bot_id, key.destiny),
            )
            return

        await self._execute(
            """
            INSERT INTO fsm_state (chat_id, user_id, bot_id, destiny, state, data)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(chat_id, user_id, bot_id, destiny) DO UPDATE SET data=excluded.data
            """,
            (key.chat_id, key.user_id, key.bot_id, key.destiny, state_str, data_str),
        )

    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        await self._init_db()
        row = await self._fetch_one(
            "SELECT data FROM fsm_state WHERE chat_id=? AND user_id=? AND bot_id=? AND destiny=?",
            (key.chat_id, key.user_id, key.bot_id, key.destiny),
        )
        if row and row["data"]:
            from typing import cast

            return cast(dict[str, Any], json.loads(row["data"]))
        return {}

    async def close(self) -> None:
        pass
