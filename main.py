from typing import Union

from fastapi import FastAPI

from handlers.english_player_handler import start_english_player_handler, stop_english_player_handler
from servers.audio_player import is_playing

app = FastAPI()


@app.post("/english_player/start")
def start_english_player():
    return start_english_player_handler()


@app.post("/english_player/stop")
def stop_english_player():
    return stop_english_player_handler()


@app.get("/english_player/is_playing")
def is_playing_handler():
    return is_playing()
