import aioinject

from app import infrastructure, service_layer
from app.configs import Settings

from .wrappers import AuthServiceWrapper, PostgresDatabaseWrapper, RouterServiceHTTPClientWrapper

container = aioinject.Container()

# settings
container.register(aioinject.Object(Settings()))

# infrastructure
container.register(
    aioinject.Singleton(PostgresDatabaseWrapper, infrastructure.APostgresDatabase),
    aioinject.Singleton(infrastructure.SchedulerManager, infrastructure.ASchedulerManager),
    aioinject.Singleton(RouterServiceHTTPClientWrapper, infrastructure.ARouterServiceHTTPClient),
)

# service layer
container.register(
    aioinject.Transient(service_layer.UnitOfWork, service_layer.AUnitOfWork),
    aioinject.Singleton(AuthServiceWrapper, service_layer.A_AuthService),
    aioinject.Transient(service_layer.UsersService, service_layer.AUsersService),
    aioinject.Transient(service_layer.DataStoreService, service_layer.ADataStoreService),
)
