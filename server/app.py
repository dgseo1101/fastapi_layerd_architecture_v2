# -*- coding: utf-8 -*-
from fastapi import FastAPI

from server.infrastructure.di.container import ServerContainer
from server.application.controllers.user_controller import router as user_router

container = None


def create_container():
    container = ServerContainer()
    container.wire(packages=["server.application.controllers"])

    container.config.from_yaml("./config.yml")

    return container


def create_app():
    global container
    container = create_container()

    app = FastAPI(docs_url="/docs")
    app.include_router(user_router)

    return app


app = create_app()
