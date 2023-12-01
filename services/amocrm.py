import asyncio
import json

import aiohttp
import bs4
import requests
from services.misc import timing_decorator


class AmoCRMConnection:
    login, password, amo_hash, host = '', '', '', ''

    _cookies, _headers, _chat_token, _csrf_token, _access_token, _refresh_token = None, None, None, None, None, None

    def __init__(self, *, user_login: str, user_password: str, host: str, token: str):
        self.login = user_login
        self.password = user_password
        self.host = host
        self.amo_hash = token

    async def _create_session(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.host) as response:
                self._cookies = response.cookies
                self._csrf_token = self._cookies.get('csrf_token').value
                self._headers = {
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Cookie': f'session_id={self._cookies.get("session_id").value}; csrf_token={self._csrf_token};',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
                }

    async def _create_chat_token(self):
        url = f'{self.host}ajax/v1/chats/session'
        payload = {'request[chats][session][action]': 'create'}
        async with aiohttp.ClientSession(cookies=self._cookies) as session:
            async with session.post(url=url, headers=self._headers, data=payload) as response:
                print('yesssssss')
                try:
                    content = await response.json()
                    self._chat_token = content['response']['chats']['session']['access_token']
                except:
                    pass  # TODO: оповестить об ошибке

    async def authorize(self):
        await self._create_session()
        print('session yes')
        url = f'{self.host}oauth2/authorize'
        payload = {
            'csrf_token': self._csrf_token,
            'username': self.login,
            'password': self.password
        }
        async with aiohttp.ClientSession(cookies=self._cookies) as session:
            async with session.post(url=url, data=payload, headers=self._headers) as response:
                if response.status != 200:
                    return False  # TODO: оповестить об ошибке
                print('hahaha')
                self._cookies = response.cookies
                self._access_token = self._cookies.get('access_token').value
                self._refresh_token = self._cookies.get('refresh_token').value

                self._headers['access_token'], self._headers['refresh_token'] = self._access_token, self._refresh_token
                self._headers['Host'] = self.host.replace('https://', '').replace('/', '')
                await self._create_chat_token()
                print('hahahahah22')
                return True

    async def get_unanswered_messages(self, search_info: list[list]):
        url = f'{self.host}ajax/v4/inbox/list'
        params = {
            'limit': 50,
            'order[sort_by]': 'first_unanswered_message_at',
            'order[sort_type]': 'desc',
            'filter[is_read][]': 'false'
        }

        for index, param in enumerate(search_info):
            params[f'filter[pipe][{param[0]}][{index}]'] = param[1]

        async with aiohttp.ClientSession(cookies=self._cookies) as session:
            response = await session.get(url=url, headers=self._headers, params=params)
            content = await response.json()
        return content['_embedded']['talks']

    async def send_message(self, message: str, chat_id: str):
        headers = {'X-Auth-Token': self._chat_token}
        url = f'https://amojo.amocrm.ru/v1/chats/{self.amo_hash}/{chat_id}/messages?with_video=true&stand=v16'
        async with aiohttp.ClientSession(cookies=self._cookies) as session:
            response = await session.post(url=url, data=json.dumps({"text": message}), headers=headers)
            return response.status == 200

    async def get_last_message(self, chat_id):
        try:
            url = f'{self.host}ajax/v2/talks'
            data = {'chats_ids[]': chat_id}

            async with aiohttp.ClientSession(cookies=self._cookies) as session:
                response = await session.post(url=url, data=data, headers=self._headers)

            response = await response.json()
            for k, v in response.items():
                v = v[0]
                return v['last_message'], v['last_message_author']['type']
        except:
            return '', 'contact'

    async def _create_field(self, name):
        url = f'{self.host}ajax/settings/custom_fields/'
        data = {
            'action': 'apply_changes',
            'cf[add][0][element_type]': 2,
            'cf[add][0][sortable]': True,
            'cf[add][0][groupable]': True,
            'cf[add][0][predefined]': False,
            'cf[add][0][type_id]': 1,
            'cf[add][0][name]': name,
            'cf[add][0][disabled]': '',
            'cf[add][0][settings][formula]': '',
            'cf[add][0][pipeline_id]': 0
        }
        async with aiohttp.ClientSession(cookies=self._cookies) as session:
            await session.post(url=url, data=data, headers=self._headers)

    async def set_field_by_name(self, *, pipeline_id: int, deal_id: int, field: dict, new_value: str):
        url = f'{self.host}ajax/leads/detail/'
        active_value = new_value
        if field['type'] == 'select':
            for f in field['values']:
                if f['value'] == new_value:
                    active_value = f['id']

        data = {
            f'CFV[{field["id"]}]': active_value,
            'lead[STATUS]': '',
            'lead[PIPELINE_ID]': pipeline_id,
            'ID': deal_id
        }
        async with aiohttp.ClientSession(cookies=self._cookies) as session:
            await session.post(url=url, data=data, headers=self._headers)

    async def get_params_information(self, fields_to_get: list, deal_id: int):
        result = {}
        url = f'{self.host}leads/detail/{deal_id}'
        async with aiohttp.ClientSession(cookies=self._cookies) as session:
            response = await session.get(url=url, headers=self._headers)
        soup = bs4.BeautifulSoup(await response.text(), features='html.parser')

        for field in soup.find_all('div', {'class': 'linked-form__field linked-form__field-text'}):
            label = field.find('div', {'class': 'linked-form__field__label'}).text.strip()
            value = field.find('div', {'class': 'linked-form__field__value'}).find('input')['value'].strip()
            index = field.get('data-id')
            if label in fields_to_get:
                if value == '':
                    value = None

                result[label] = {'active': value, 'values': [], 'type': 'field', 'id': index}

        selects = soup.find_all('div', {'class': 'linked-form__field linked-form__field-select'})
        for select in selects:
            k = select.find('div', {'class': 'linked-form__field__label'}).text
            v = select.find('span', {'class': 'control--select--button-inner'}).text.strip()
            index = select.get('data-id')
            if k in fields_to_get:
                result[k] = {'active': v,
                             'values': [],
                             'type': 'select',
                             'id': index}
                if result[k]['active'] == 'Выбрать':
                    result[k]['active'] = None
                for v in select.find_all('li', {'class': 'control--select--list--item'}):
                    index = v.get('data-value')
                    if v.text.strip() != 'Выбрать':
                        result[k]['values'].append({'value': v.text.strip(), 'id': index})

        need_update = False
        for field in fields_to_get:
            if field not in result.keys():
                await self._create_field(field)
                need_update = True
        if need_update:
            return self.get_params_information(fields_to_get, deal_id)
        return result


async def test():
    login = 'appress8@gmail.com'
    password = '83xUHS73'
    token = '5f8939c9-d6e8-4452-8797-f287ace06805'
    host = 'https://appress8.amocrm.ru/'
    amo_connection = AmoCRMConnection(host=host, user_login=login, user_password=password, token=token)
    auth_status: bool = await amo_connection.authorize()

    if not auth_status:
        return Exception()
    my_deal = '2ceb24f8-b7f9-48d3-8a0e-51e78dc53181'
    pipeline_id = 7343546
    deal_id = 5117051
    # response = await amo_connection.get_params_information(['age', 'Цвет волос'], deal_id)
    # await amo_connection.set_field_by_name(pipeline_id=pipeline_id, deal_id=deal_id, field=response['Цвет волос'], new_value='Серый')
    # await amo_connection.get_last_message(my_deal)
    # await amo_connection._create_field("Привет")
    # await amo_connection.send_message('Привет', my_deal)
    # await amo_connection._create_chat_token()
    # print(await amo_connection.get_unanswered_messages([['7343546', '61111206'], ['7343546', '61111210']]))
    # await amo_connection._create_chat_token()
    # print(amo_connection._chat_token)


@timing_decorator
def main():
    asyncio.run(test())
