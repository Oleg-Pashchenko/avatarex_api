import asyncio
import json

import aiohttp
import httpx
import openai
import requests as requests

from db import logs, site, api
from db.site import PromptModeSettings
from modes import misc
from services.misc import timing_decorator


@timing_decorator
async def prompt_request(*,
                         api_key: str = None,
                         model: str = "gpt-3.5-turbo",
                         messages_history: list[dict] = None,
                         tokens_limit: int = 1000,
                         temperature: float = 1.0,
                         error_message: str = "Произошла ошибка настроек. Повторите запрос позднее!") -> str:
    headers = {'Authorization': f'Bearer {api_key}', "Content-Type": "application/json"}
    data = {
        'model': model,
        'messages': messages_history,
        'max_tokens': tokens_limit,
        'temperature': temperature
    }
    error = None
    url = 'https://api.openai.com/v1/chat/completions'
    print('yes')
    client = httpx.AsyncClient()
    print(client)
    response = await client.post(url=url, headers=headers, json=json.dumps(data))
    print(response)
    answer = await response.json()
    print(answer)

    logs.save_log(
        avatarex_id=1,
        pipeline_id=1,
        stage_id=1,
        mode='По контексту',
        answer=answer,
        error=error
    )
    return answer


@timing_decorator
async def prompt_mode(user_id: int, pipeline_id: int, stage_id: int, lead_id):
    settings: PromptModeSettings = site.get_prompt_mode_settings(user_id=user_id, pipeline_id=pipeline_id,
                                                                 stage_id=stage_id)
    messages: list[dict] = api.get_messages_history(lead_id=lead_id)
    messages_history: list[dict] = misc.get_messages_context(messages=messages, context=settings.context,
                                                             model=settings.model, max_tokens=settings.max_tokens)

    answer: str = await prompt_request(
        api_key=settings.api_key,
        model=settings.model,
        messages_history=messages_history,
        tokens_limit=settings.max_tokens,
        temperature=settings.temperature,
        error_message=settings.error_message
    )
    return answer


"""
print(asyncio.run(prompt_request(api_key='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',
                           messages_history=[
                               {
                                   "role": "system",
                                   "content": "You are a helpful assistant."
                               },
                               {
                                   "role": "user",
                                   "content": "Hello!"
                               }
                           ])))
"""
