from quart import Quart, request

from modes.prompt import prompt_request
from modes.knowledge import knowledge_request

api_key = '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'
app = Quart(__name__)


@app.route('/reserve')
async def reserve_prompt_mode():
    pass  # Here get user_id by deal_id and execute it


@app.route('/api/v1/amocrm/<username>', methods=['POST'])
async def amo_handler():
    data = dict(await request.values)
    print(data)


if __name__ == "__main__":
    app.run()
