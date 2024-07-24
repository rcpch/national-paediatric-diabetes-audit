import httpx

from asgiref.sync import async_to_sync

def httpx_async_to_sync(async_fn):
    async def wrapper(*args, **kwargs):
        async with httpx.AsyncClient() as client:
            return await async_fn(*args, **kwargs)
    
    return async_to_sync(wrapper)