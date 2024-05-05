from django.apps import AppConfig


class NpdaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "project.npda"

    def ready(self) -> None:
        import project.npda.signals

        return super().ready()
