# -*- coding: utf-8 -*-
from dependency_injector import providers

from core.infrastructure.database.session import ManagedSession
from core.infrastructure.di.container import CoreContainer
from server.application.services.user_service import UserService
from server.infrastructure.repositories.user_repository import UserRepository


class ServerContainer(CoreContainer):
    session_factory = providers.Factory(
        ManagedSession,
        session_maker=CoreContainer.database.provided.session_maker,
    )

    user_service = providers.Factory(
        UserService,
        session_factory=session_factory.provider,
        repo_class=UserRepository,
        config=CoreContainer.config,
    )
