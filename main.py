from typing import Union

import fastapi
from fastapi import FastAPI

from entities.base import new_success_response
from handlers.english_player_handler import start_english_player_handler, stop_english_player_handler
from servers.audio_player import get_status, set_progress, AudioPlayerConfig

app = FastAPI()


@app.post("/english_player/start")
def start_english_player():
    return start_english_player_handler()


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
