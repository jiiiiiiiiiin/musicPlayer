import re

from pyncm import apis
import json


def search(text):
    """
    Search for a song or artist on NCM.
    :param text:
    :param pages:
    :param limit:
    :return:
    """
    ret = apis.cloudsearch.GetSearchResult(keyword=text)
    if ret.get('code') != 200:
        return None
    result = ret.get("result")
    result_count = result.get("songCount")
    result_songs = result.get("songs")
    ret = []
    for song in result_songs:
        time = song.get("dt") / 1000
        minutes = int(time / 60)
        seconds = int(time % 60)
        dt = f'{minutes:02d}:{seconds:02d}'

        tmp_song = {
            "name": song.get("name"),
            "id": song.get("id"),
            "artist": song.get("ar")[0].get("name"),
            "picUrl": song.get("al").get("picUrl"),
            "dT": dt,
        }
        ret.append(tmp_song)
    return ret


def get_song_lyrics(song_id):
    ret = apis.track.GetTrackLyrics(song_id)
    if ret.get('code') != 200:
        return None
    lyric = ret.get("lrc").get("lyric")
    return lyric


def get_song(song_id):
    ret = apis.track.GetTrackAudio([song_id])
    if ret.get('code') != 200:
        return None
    audio = ret.get("data")[0].get("url")
    return audio


# 毫秒转分钟
def ms_to_min(ms):
    minutes = int(ms / 1000 / 60)
    seconds = int(ms / 1000 % 60)
    return f'{minutes:02d}:{seconds:02d}'




if __name__ == '__main__':
    # search("刚刚好")
    get_song("415792881")
    pass