from entities.base import new_success_response
from servers.audio_player import start_play, stop_play


def start_english_player_handler():
    start_play()
    return new_success_response()


def stop_english_player_handler():
    stop_play()
    return new_success_response()
