import dataclasses

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
class AmoSettings:
    id: int
    user_id: int
    email: str
    password: str
    host: str
    account_chat_id: str


@dataclasses.dataclass
class PipelineSettings:
    id: int
    p_id: int
    user_id: int
    name: str
    order_number: int
    chosen_work_mode: str
    voice_message_detection: bool
    prompt_mode_id: int
    knowledge_mode_id: int
    search_mode_id: int
    knowledge_and_search_mode_id: int
    is_exists: bool


@dataclasses.dataclass
class PromptModeSettings:
    id: int
    context: str
    model: str
    max_tokens: int
    temperature: float
    qualification_id: int
    error_message: str
    error_message_time: str
    connected_to: int
    working_stages: dict
    api_key: str


dotenv.load_dotenv()
engine = sqlalchemy.create_engine(f'postgresql://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}'
                                  f'@{os.getenv("DB_HOST")}:5432/{os.getenv("SITE_DB_NAME")}', pool_pre_ping=True)
Session = sessionmaker(bind=engine)
session = Session()

Base = automap_base()
Base.prepare(engine, reflect=True)

AmoConnect = Base.classes.home_amoconnect
GptApiKey = Base.classes.home_gptapikey
ModeMessages = Base.classes.home_modemessages
KnowledgeMode = Base.classes.home_knowledgemode
Pipelines = Base.classes.home_pipelines
Statuses = Base.classes.home_statuses
PromptMode = Base.classes.home_promptmode

for c in [AmoConnect, GptApiKey, ModeMessages, KnowledgeMode, Pipelines, Statuses, PromptMode]:
    c.as_dict = as_dict


def is_stage_working(pipeline_id: int, stage_id: int):
    pipeline = _get_pipeline(pipeline_id)
    q = session.query(Statuses).filter(Statuses.pipeline_id_id == pipeline.id and Statuses.status_id == stage_id)
    result = q.first()
    return result.as_dict()['is_active']


def get_amo_settings(user_id: int) -> AmoSettings:
    q = session.query(AmoConnect).filter(AmoConnect.user_id == user_id)
    result = q.first().as_dict()
    return AmoSettings(**result)


def get_working_mode(pipeline_id: int) -> str:
    pipeline = _get_pipeline(pipeline_id)
    return pipeline.chosen_work_mode


def _get_pipeline(pipeline_id: int):
    q = session.query(Pipelines).filter(Pipelines.p_id == pipeline_id)
    result = q.first().as_dict()
    return PipelineSettings(**result)


def get_prompt_mode_settings(user_id: int, pipeline_id: int, stage_id: int):
    pipeline = _get_pipeline(pipeline_id)
    q = session.query(PromptMode).filter(PromptMode.id == pipeline.prompt_mode_id)
    result = q.first().as_dict()
    return PromptModeSettings(**result, api_key=_get_gpt_api_key(user_id))


def _get_gpt_api_key(user_id: int):
    q = session.query(GptApiKey).filter(GptApiKey.user_id == user_id)
    result = q.first().as_dict()
    return result['key']


def get_knowledge_mode_settings():
    pass

# print(is_stage_working(7381894, 61378086))
# print(get_amo_settings(1))
# p_id = 7412586
# print(get_prompt_mode_settings(1, p_id, 1))
