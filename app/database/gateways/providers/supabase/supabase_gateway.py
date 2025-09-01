from __future__ import annotations
from typing import Any, Dict, Mapping, Type, TypeVar, Generic, cast, Iterable
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
        try:
            self._client.postgrest.auth(self._client.supabase_key)
            self._client.postgrest.client.headers.update({"apikey": self._client.supabase_key})
        except Exception:
            pass

    @classmethod
    def from_config(cls, cfg: SupabaseConfig, table: str, model: Type[T]) -> "SupabaseTable[T]":
        if not getattr(cfg, "url", None) or not getattr(cfg, "key", None):
            raise ValueError("SupabaseConfig must have 'url' and 'key'")
        if not str(cfg.url).startswith("https://"):
            raise ValueError("Supabase URL must start with https://")
        return cls(create_client(str(cfg.url), str(cfg.key)), table, model)

    # ---------- helpers ----------
    @staticmethod
    def _match(q, filters: Dict[str, Any]):
        for k, v in (filters or {}).items():
            if isinstance(v, (list, tuple, set)):
                q = q.in_(k, list(v))
            elif v is None:
                q = q.is_(k, "null")
            else:
                q = q.eq(k, v)
        return q

    def _to_model(self, row: Mapping[str, Any]) -> T:
        return self._model.model_validate(row)

    @staticmethod
    def _first_row(res) -> Dict[str, Any]:
        data = getattr(res, "data", None)
        if isinstance(data, list) and data and isinstance(data[0], dict):
            return cast(Dict[str, Any], data[0])
        if isinstance(data, dict):
            return cast(Dict[str, Any], data)
        raise RuntimeError("No row returned from Supabase")

    # ---------- CRUD ----------
    def insert(self, data: Dict[str, Any]) -> T:
        res = self._t.insert(data).execute()
        try:
            row = self._first_row(res)
            return self._to_model(row)
        except Exception:
            pk = data.get("id") or data.get("uuid") or data.get("session_id")
            if pk is not None:
                found = (
                    self.select_one({"id": pk})
                    or self.select_one({"uuid": pk})
                    or self.select_one({"session_id": pk})
                )
                if found:
                    return found
            return self._model.model_validate(data)

    def update(self, filters: Dict[str, Any], updates: Dict[str, Any]) -> T:
        if not filters:
            raise ValueError("Refusing to UPDATE without filters")
        q = self._match(self._t.update(updates), filters)
        res = q.execute()
        try:
            row = self._first_row(res)
            return self._to_model(row)
        except Exception:
            one = self.select_one(filters)
            if one is None:
                raise RuntimeError("Update succeeded but no row returned/found")
            return one

    def select_one(self, filters: Dict[str, Any]) -> T | None:
        q = self._match(self._t.select("*"), filters)
        try:
            res = q.single().execute()
            data = getattr(res, "data", None)
            if isinstance(data, dict):
                return self._to_model(cast(Dict[str, Any], data))
        except Exception:
            res = q.limit(1).execute()
            rows = res.data or []
            if not rows or not isinstance(rows[0], dict):
                return None
            return self._to_model(cast(Dict[str, Any], rows[0]))
        return None

    def select_many(self, filters: Dict[str, Any]) -> list[T]:
        q = self._match(self._t.select("*"), filters)
        res = q.execute()
        rows = res.data or []
        return [self._to_model(cast(Dict[str, Any], r)) for r in rows if isinstance(r, dict)]

    def delete(self, filters: Dict[str, Any]) -> bool:
        if not filters:
            raise ValueError("Refusing to DELETE without filters")
        q = self._match(self._t.delete(), filters)
        q.execute()
        return True
