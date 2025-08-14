from dataclasses import dataclass
import app.core.environment as env

@dataclass(frozen=True)
class SupabaseConfig:
    # Supabase Configuration
    url: env.SUPABASE_URL
    key: env.SUPABASE_SERVICE_ROLE_KEY