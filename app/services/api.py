import logging

from app.bootstrap.wire_app import wire_app
from app.common.plugin_discovery import discover_plugins
from app.core.config import AppConfig
from app.logic.dialogue_dna import DialogueDNALogic
from app.services.authz import AuthZ


class ServicesAPI:
    def __init__(self):
        imported = discover_plugins()
        logging.getLogger("bootstrap").info("plugins loaded: %s", imported)

        # App configuration
        app_cfg = AppConfig()

        # Wire infrastructure
        app_state = wire_app(AppConfig())

        # RBAC
        authz = AuthZ(policy=app_cfg.policy.POLICY)

        logic = DialogueDNALogic(app_state)

        self._logic = logic
        self._authz = authz


    def get_logic(self):
        return self._logic
