# -*- coding: utf-8 -*-
from dependency_injector import containers, providers
from core.infrastructure.database.database import Database


class CoreContainer(containers.DeclarativeContainer):
    config = providers.Configuration(strict=True)

    database = providers.Singleton(
        Database,
        database_user=config.database.user,
        database_password=config.database.password,
        database_host=config.database.host,
        database_port=config.database.port,
        database_name=config.database.name,
    )