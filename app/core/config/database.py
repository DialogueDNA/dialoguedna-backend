from dataclasses import dataclass
import app.core.environment as env
from app.core.config.providers.supabase import SupabaseConfig


@dataclass(frozen=True)
class DatabaseConfig:
    main_database: str = env.DB_ADAPTER
    supabase: SupabaseConfig = SupabaseConfig()

    # Domain Backends
    domain_backends: dict[str, str] = None

    def __post_init__(self):
        if self.domain_backends is None:
            object.__setattr__(self, "domain_backends", {
                "users": env.USERS_DB_BACKEND,
                "sessions": env.SESSIONS_DB_BACKEND,
                "user_defaults": env.USER_DEFAULTS_DB_BACKEND,
            })

    @property
    def backends_in_use(self) -> set[str]:
        return set(self.domain_backends.values())