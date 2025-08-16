from __future__ import annotations
from typing import Optional, Dict, Any

from app.database.repos.registry import register_repo


@register_repo(domain="user_defaults", table="user_defaults")
class UserDefaultsRepo:
    def __init__(self, table_gateway):
        self.t = table_gateway

    def get(self, user_id: str) -> Optional[Dict[str, Any]]:
        res = self.t.select_one({"user_id": user_id})
        if not res:
            return None
        if isinstance(res, dict) and "data" in res and res["data"] is not None:
            return res["data"]
        return res

    def upsert(self, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        current = self.get(user_id)
        if current is None:
            body = {"user_id": user_id, **payload}
            ins = self.t.insert(body)
            if isinstance(ins, dict) and "data" in ins and ins["data"] is not None:
                return ins["data"]
            return ins or body
        else:
            upd = self.t.update({"user_id": user_id}, payload)
            if isinstance(upd, dict) and "data" in upd and upd["data"] is not None:
                return upd["data"]
            out = dict(current)
            out.update(payload)
            return out
