import time

NEW_CLIENT_KEY = 'unsorted[add][0][pipeline_id]'
UPDATE_PIPELINE_KEY = 'leads[update][0][pipeline_id]'
VOICE_MESSAGE_KEY = 'message[add][0][attachment][link]'
DEFAULT_WORKING_MODE = "Standart"
DATABASE_WITH_AMO_CARDS_MODE = 'CardsDatabase'
MESSAGE_CREATION_KEY = 'message[add][0][created_at]'
UNSORTED_LEAD_ID_KEY = f'unsorted[add][0][lead_id]'
UPDATE_LEAD_ID_KEY = f'leads[update][0][id]'
UPDATE_STATUS_ID_KEY = 'leads[update][0][status_id]'
MESSAGE_ID_KEY = 'message[add][0][id]'
USER_ID_HASH_KEY = 'message[add][0][chat_id]'
MESSAGE_KEY = 'message[add][0][text]'
LEAD_KEY = 'message[add][0][element_id]'
MODEL_16K_SIZE_VALUE = 16385
MODEL_16K_KEY = '16k'
MODEL_4K_SIZE_VALUE = 4096
RESTART_KEY = '/restart'


def timing_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Function {func.__name__} took {execution_time:.6f} seconds to execute.")
        return result
    return wrapper


def as_dict(obj):
    data = obj.__dict__
    data.pop('_sa_instance_state')
    return data
