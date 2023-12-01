import dataclasses
import datetime
import random
from services.misc import *
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
import warnings
from sqlalchemy.exc import SADeprecationWarning

import dotenv
import os

from services.misc import as_dict

warnings.filterwarnings('ignore', category=SADeprecationWarning)


@dataclasses.dataclass
class Leads:
    id: int
    pipeline_id: int
    status_id: int


dotenv.load_dotenv()
engine = sqlalchemy.create_engine(f'postgresql://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}'
                                  f'@{os.getenv("DB_HOST")}:5432/{os.getenv("AMO_BOT_DB_NAME")}', pool_pre_ping=True)
Session = sessionmaker(bind=engine)
session = Session()

Base = automap_base()
Base.prepare(engine, reflect=True)


@dataclasses.dataclass
class Messages:
    id_id: int
    id: str
    message: str
    lead_id: int
    is_bot: bool
    date: datetime.datetime


LeadsEntity = Base.classes.leads
MessagesEntity = Base.classes.messages

for c in [LeadsEntity, MessagesEntity]:
    c.as_dict = as_dict


def get_messages_history(lead_id: int):
    message_objects = session.query(MessagesEntity).filter(MessagesEntity.lead_id == lead_id).all()
    message_objects = sorted(message_objects, key=lambda x: x.date)
    messages = []
    for message_obj in message_objects:
        if message_obj.is_bot:
            messages.append({'role': 'assistant', 'content': message_obj.message})
        else:
            messages.append({'role': 'user', 'content': message_obj.message})
    return messages


def add_message(message, lead_id, is_bot):
    if is_bot:
        message_id = f'assistant-{random.randint(1000000, 10000000)}'
    else:
        message_id = f'assistant-{random.randint(1000000, 10000000)}'
    obj = Messages(id=message_id, message=message, lead_id=lead_id, is_bot=is_bot, date=datetime.datetime.now())
    session.add(obj)
    session.commit()


@timing_decorator
def update_lead(r_d):
    if r_d.get(NEW_CLIENT_KEY, None) and r_d.get(UNSORTED_LEAD_ID_KEY, None):  # New client
        if not get_lead(r_d[UNSORTED_LEAD_ID_KEY]):
            new_lead = LeadsEntity(id=r_d[UNSORTED_LEAD_ID_KEY], pipeline_id=r_d[NEW_CLIENT_KEY], status_id=0)
            session.add(new_lead)

    elif r_d.get(UPDATE_LEAD_ID_KEY, None) and r_d.get(UPDATE_PIPELINE_KEY, None) \
            and r_d.get(UPDATE_STATUS_ID_KEY, None):  # Update client
        lead_obj = session.query(LeadsEntity).filter(LeadsEntity.id == r_d[UPDATE_LEAD_ID_KEY]).first()
        lead_obj.pipeline_id, lead_obj.status_id = r_d[UPDATE_PIPELINE_KEY], r_d[UPDATE_STATUS_ID_KEY]

    session.commit()


def get_lead(lead_id):
    return session.query(LeadsEntity).filter(LeadsEntity.id == lead_id).first()
