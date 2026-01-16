# -*- coding: utf-8 -*-
from core.infrastructure.di.container import CoreContainer
from core.infrastructure.database.unit_of_work import UnitOfWork
from core.application.services.base_service import RepoRegistry

from server.infrastructure.repositories.user_repository import UserRepository


from server.application.services.user_service import UserService

from dependency_injector import providers

class ServerContainer(CoreContainer):
    uow_factory = providers.Factory(
        UnitOfWork,
        session_maker=CoreContainer.database.provided.session_maker, 
    )

    repo_factories = providers.Object({
        "user": providers.Factory(UserRepository),
    })

    repo_registry = providers.Singleton(
        RepoRegistry,
        factories=repo_factories,
    )

    user_service = providers.Factory(
        UserService,
        uow_factory=uow_factory.provider,
        repo_registry=repo_registry,
        config=CoreContainer.config
    )