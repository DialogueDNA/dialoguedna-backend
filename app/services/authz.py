class AuthZ:
    def __init__(self, policy: dict[str, set[str]]):
        self._policy = policy

    def require(self, ctx, permission: str):
        if "admin" in (ctx.roles or []):
            return
        plan = (ctx.plan or "free").lower()
        allowed_set = self._policy.get(plan, set())
        if "*" in allowed_set or permission in allowed_set:
            return
        from fastapi import HTTPException
        raise HTTPException(403, f"Forbidden: missing permission: {permission}")
