from __future__ import annotations
from typing import Any, Dict, Mapping, Type, TypeVar, Generic, cast
from pydantic import BaseModel
from supabase import create_client, Client as SupabaseClient

from app.core.config.providers.supabase.supabase import SupabaseConfig
from app.interfaces.db.table_gateway import TableGateway

T = TypeVar("T", bound=BaseModel)

class SupabaseTable(TableGateway[T], Generic[T]):
    def __init__(self, client: SupabaseClient, table: str, model: Type[T]):
        self._client = client
        self._t = client.table(table)
        self._model = model
        self._client.postgrest.auth(self._client.supabase_key)
        try:
            self._client.postgrest.client.headers.update({"apikey": self._client.supabase_key})
        except Exception:
            pass

    @classmethod
    def from_config(cls, cfg: SupabaseConfig, table: str, model: Type[T]) -> "SupabaseTable[T]":
        if not cfg.url or not cfg.key or None:
            raise ValueError("SupabaseConfig must have 'url' and 'key'")
        if not str(cfg.url).startswith("https://"):
            raise ValueError("Supabase URL must start with https://")
        return cls(create_client(cfg.url, cfg.key), table, model)

    # ---------- helpers ----------
    @staticmethod
    def _match(q, filters: Dict[str, Any]):
        for k, v in (filters or {}).items():
            q = q.eq(k, v)
        return q

    def _to_model(self, row: Mapping[str, Any]) -> T:
        return self._model.model_validate(row)

    @staticmethod
    def _first_row(res) -> Dict[str, Any]:
        rows = res.data or []
        if not rows or not isinstance(rows[0], dict):
            raise RuntimeError("No row returned from Supabase")
        return cast(Dict[str, Any], rows[0])

    # ---------- CRUD ----------
    def insert(self, data: Dict[str, Any]) -> T:
        res = self._t.insert(data).select("*").execute()
        row = self._first_row(res)
        return self._to_model(row)

    def update(self, filters: Dict[str, Any], updates: Dict[str, Any]) -> T:
        q = self._match(self._t.update(updates).select("*"), filters)
        res = q.execute()
        row = self._first_row(res)
        return self._to_model(row)

    def select_one(self, filters: Dict[str, Any]) -> T | None:
        q = self._match(self._t.select("*"), filters)
        res = q.limit(1).execute()
        rows = res.data or []
        if not rows or not isinstance(rows[0], dict):
            return None
        return self._to_model(cast(Dict[str, Any], rows[0]))

    def select_many(self, filters: Dict[str, Any]) -> list[T]:
        q = self._match(self._t.select("*"), filters)
        res = q.execute()
        rows = res.data or []
        return [self._to_model(cast(Dict[str, Any], r)) for r in rows if isinstance(r, dict)]

    def delete(self, filters: Dict[str, Any]) -> bool:
        q = self._match(self._t.delete(), filters)
        q.execute()
        return True
