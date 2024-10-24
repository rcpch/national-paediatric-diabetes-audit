import contextvars
import httpx

async_client = contextvars.ContextVar("httpx_client", default=httpx.AsyncClient())