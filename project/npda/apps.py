import threading

from django.apps import AppConfig

from .management.commands.write_azure_pg_password_file import write_azure_pg_password_file 

def periodically_update_azure_pg_password_file():
    update_interval = 60 * 15 # 15 minutes

    def _periodically_update_azure_pg_password_file():
        write_azure_pg_password_file()
        
        thread = threading.Timer(update_interval, _periodically_update_azure_pg_password_file)
        thread.daemon = True
        thread.start()
    
    thread = threading.Timer(update_interval, _periodically_update_azure_pg_password_file)
    thread.daemon = True
    thread.start()

class NpdaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "project.npda"

    def ready(self) -> None:
        import project.npda.signals

        periodically_update_azure_pg_password_file()

        return super().ready()
