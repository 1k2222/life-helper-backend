import os
import tempfile
from typing import Union

import requests
import fastapi
from fastapi import FastAPI

from dtos import PronounceCantoneseRequest
from entities.base import new_success_response
from handlers.english_player_handler import start_english_player_handler, stop_english_player_handler, \
    start_english_player_newest_handler
from servers.audio_player import get_status, AudioPlayerConfig

from fastapi.responses import FileResponse

app = FastAPI()


@app.post("/english_player/start")
def start_english_player():
    return start_english_player_handler()


@app.post("/english_player/start_newest")
def start_english_player():
    return start_english_player_newest_handler()


@app.post("/english_player/stop")
def stop_english_player():
    return stop_english_player_handler()


@app.get("/english_player/get_status")
def get_status_handler():
    return get_status()


@app.post("/english_player/set_progress")
async def set_progress_handler(req: AudioPlayerConfig):
    set_progress(req)
    return new_success_response()


@app.post("/pronounce_cantonese")
async def set_progress_handler(req: PronounceCantoneseRequest):
    url = f'{os.getenv("GPT_SOVITS_PATH")}/tts'
    req_body = {
        "text": '.'.join([x for x in req.text]),
        "text_lang": "all_yue",
        "ref_audio_path": os.path.realpath('./assets/cantonese_reference.mp3'),
        "aux_ref_audio_paths": [],
        "prompt_text": "如流傻泪祈望可体恤兼见谅明晨离别你路",
        "prompt_lang": "all_yue",
        "top_k": 5,
        "top_p": 1,
        "temperature": 1,
        "text_split_method": "cut5",
        "batch_size": 1,
        "batch_threshold": 0.75,
        "split_bucket": True,
        "speed_factor": 1,
        "fragment_interval": 0.3,
        "seed": -1,
        "media_type": "aac",
        "streaming_mode": False,
        "parallel_infer": True,
        "repetition_penalty": 1.35,
        "sample_steps": 32,
        "super_sampling": False
    }
    resp = requests.post(url, json=req_body)
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(resp.content)
    return FileResponse(temp_file.name, media_type='audio/aac', filename=f'{os.path.basename(temp_file.name)}.aac')
