import glob
import multiprocessing
import os
import threading
import time
from multiprocessing import Process
from typing import Optional, Dict

from audioplayer import AudioPlayer
from pydantic import BaseModel

from defines.pathes import CONFIG_PATH
from entities.base import new_success_response

_player_process: Optional[Process] = None
_play_newest = False


class AudioPlayerConfig(BaseModel):
    study_progress: int
    cursor: int


def load_playlist(total):
    play_list = glob.glob('./assets/all_audios/*.mp3')
    play_list.sort(reverse=True)
    play_list = play_list[-total:]
    return play_list


def _start_play():
    config_path = os.path.join(CONFIG_PATH, "audio_player_config.json")
    config = AudioPlayerConfig.model_validate_json(open(config_path, 'r').read())
    play_list = load_playlist(config.study_progress)
    while True:
        file = play_list[config.cursor]
        print(f"ready to play {file}...")
        player = AudioPlayer(file)
        player.play(block=True)
        config.cursor += 1
        if config.cursor >= config.study_progress:
            config.cursor = 0
        open(config_path, 'w').write(config.model_dump_json())
        print(f"{file} ended.")


def _start_play_newest():
    config_path = os.path.join(CONFIG_PATH, "audio_player_config.json")
    config = AudioPlayerConfig.model_validate_json(open(config_path, 'r').read())
    play_list = load_playlist(config.study_progress)
    file = play_list[0]
    while True:
        player = AudioPlayer(file)
        player.play(block=True)


def start_play():
    global _player_process, _play_newest
    if _player_process:
        return
    _play_newest = False
    _player_process = multiprocessing.Process(target=_start_play)
    _player_process.start()


def start_play_newest():
    global _player_process, _play_newest
    if _player_process:
        return
    _play_newest = True
    _player_process = multiprocessing.Process(target=_start_play_newest)
    _player_process.start()


def stop_play():
    global _player_process, _play_newest
    if not _player_process:
        return
    _player_process.terminate()
    _play_newest = False
    _player_process = None


def get_status():
    config_path = os.path.join(CONFIG_PATH, "audio_player_config.json")
    config = AudioPlayerConfig.model_validate_json(open(config_path, 'r').read())

    play_list = load_playlist(config.study_progress)
    return new_success_response({
        "is_playing": _player_process is not None,
        "audio_count": len(glob.glob('./assets/all_audios/*.mp3')),
        "study_progress": config.study_progress,
        "cursor": config.cursor,
        "current_file": os.path.basename(play_list[0 if _play_newest else config.cursor])
    })

def set_progress(new_progress: AudioPlayerConfig):
    config_path = os.path.join(CONFIG_PATH, "audio_player_config.json")
    open(config_path, 'w').write(new_progress.model_dump_json())
