import glob
import multiprocessing
import os
import threading
import time
from multiprocessing import Process
from typing import Optional

from audioplayer import AudioPlayer
from pydantic import BaseModel

from defines.pathes import CONFIG_PATH
from entities.base import new_success_response

_player_process: Optional[Process] = None


class AudioPlayerConfig(BaseModel):
    total: int
    cursor: int


def _start_play():
    play_list = glob.glob('./assets/all_audios/*.mp3')
    config_path = os.path.join(CONFIG_PATH, "audio_player_config.json")
    config = AudioPlayerConfig.model_validate_json(open(config_path, 'r').read())
    play_list.sort(reverse=True)
    play_list = play_list[-config.total:]
    while True:
        file = play_list[config.cursor]
        print(f"ready to play {file}...")
        player = AudioPlayer(file)
        player.play(block=True)
        config.cursor += 1
        if config.cursor >= config.total:
            config.cursor = 0
        open(config_path, 'w').write(config.model_dump_json())
        print(f"{file} ended.")


def start_play():
    global _player_process
    if _player_process:
        return
    _player_process = multiprocessing.Process(target=_start_play)
    _player_process.start()


def stop_play():
    global _player_process
    if not _player_process:
        return
    _player_process.terminate()
    _player_process = None


def is_playing():
    return new_success_response({"is_playing": _player_process is not None})
