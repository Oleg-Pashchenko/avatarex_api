import tiktoken as tiktoken


def tokens_counter(messages: list[dict]):
    encoding = tiktoken.get_encoding('cl100k_base')
    num_tokens = 3
    for message in messages:
        num_tokens += 3
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
    return num_tokens


def get_messages_context(messages: list[dict], context: str, model: str, max_tokens):
    if model == 'gpt-3.5-turbo':
        tokens = 4096
    elif model == 'gpt-3.5-turbo-16k':
        tokens = 16384
    elif model == 'gpt-4-32k':
        tokens = 32768
    else:
        tokens = 128000
    tokens *= 0.95  # На всякий случай резервируем 5% в запас
    tokens -= max_tokens  # Вычитаем выделенные токены на ответ

    response = [{'role': 'system', 'content': context}]
    for message in messages:
        response.append(message)
        if tokens < tokens_counter(response):
            response.pop(-1)
            break
    return response

