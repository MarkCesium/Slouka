from dishka import Provider, Scope, provide

from src.core.config import Settings, settings


class ConfigProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_settings(self) -> Settings:
        return settings
