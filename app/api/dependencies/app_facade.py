# app/api/dependencies/app_facade.py
from typing import cast
from fastapi import Request, Depends
from app.application.facade import ApplicationFacade

def get_facade(req: Request) -> ApplicationFacade:
    return cast(ApplicationFacade, req.app.state.api)
