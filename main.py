import asyncio

from quart import Quart, request
import asyncio
from hypercorn.asyncio import serve
from hypercorn.config import Config
from db import api, site
from db.site import AmoConnect
from modes.prompt import prompt_mode
from services.misc import *
from services import amocrm

api_key = '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'
app = Quart(__name__)


@timing_decorator
@app.route('/api/v1/amocrm/<owner_id>', methods=['POST'])
async def amo_handler(owner_id):
    data = dict(await request.values)
    api.update_lead(data)
    message, lead_id = data.get(MESSAGE_KEY, None), data.get(LEAD_KEY, None)
    user_id_hash = data.get(USER_ID_HASH_KEY, None)

    if not (message and lead_id and user_id_hash):
        return 'ok'
    print(f"Получено новое сообщение от user_id: {owner_id}: {message}")
    lead = api.get_lead(lead_id)
    if not lead:
        print("Нет сделки по данному lead_id")
        return 'ok'

    if not site.is_stage_working(lead.pipeline_id, lead.status_id):
        print("На данном статусе сделки бот не работает!")
        return 'ok'
    amo_settings = site.get_amo_settings(owner_id)
    amo_connection = amocrm.AmoCRMConnection(user_login=amo_settings.email, user_password=amo_settings.password,
                                             host=amo_settings.host, token=amo_settings.account_chat_id)
    status = await amo_connection.authorize()
    if not status:
        print("Не удалось установить соединение с AmoCRM!")
        return 'ok'
    amo_message, contact = await amo_connection.get_last_message(user_id_hash)
    print(contact)
    if contact == 'user':
        print("Сообщение уже распознавалось")
        return 'ok'
    print('yes')
    api.add_message(message=message, lead_id=lead_id, is_bot=False)
    working_mode = site.get_working_mode(lead.pipeline_id)
    print('Выбран', working_mode)
    if working_mode == 'Prompt mode' or working_mode == 'Ответ по контексту':
        answer = await prompt_mode(lead_id=lead_id, pipeline_id=lead.pipeline_id,
                                   stage_id=lead.status_id, user_id=owner_id)
    else:
        answer = 'Бот сейчас не работает в этом режиме!'

    await amo_connection.send_message(answer, user_id_hash)
    api.add_message(message=answer, lead_id=lead_id, is_bot=True)
    print('Ответ:', answer)
    return 'ok'


if __name__ == '__main__':
    config = Config()
    config.bind = ["0.0.0.0:8000"]
    asyncio.run(serve(app, config))

