from copy import deepcopy

from librarian.integrations.genius import data

from . import genius_responses


def test_genius_song__from_data():
    expected_id = 378195

    payload = deepcopy(genius_responses.GENIUS_SONG)
    payload["response"]["song"]["id"] = expected_id

    song = data.GeniusSong.from_data(payload)
    assert song.id == expected_id
