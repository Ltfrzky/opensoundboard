from __future__ import annotations

from pathlib import Path

import pytest

from app.domain.enums.playback import PlaybackMode, PlaybackState
from app.domain.errors import InvalidSoundError
from app.domain.models.board import Board
from app.domain.models.sound import Sound


def test_board_requires_a_non_blank_name() -> None:
    with pytest.raises(ValueError, match="Board name cannot be blank"):
        Board(id=1, name="   ")


def test_sound_uses_a_trimmed_name_and_rejects_blank_names() -> None:
    sound = Sound(id=3, board_id=1, name="  Applause  ", file_path=Path("audio.wav"))

    assert sound.name == "Applause"
    with pytest.raises(InvalidSoundError, match="Sound name cannot be blank"):
        Sound(id=3, board_id=1, name=" ", file_path=Path("audio.wav"))


def test_sound_reports_missing_file() -> None:
    sound = Sound(id=3, board_id=1, name="Applause", file_path=Path("does-not-exist.wav"))

    assert sound.is_missing is True


def test_playback_enums_express_the_prototype_policies() -> None:
    assert PlaybackMode.OVERLAP.value == "overlap"
    assert PlaybackMode.STOP_PREVIOUS.value == "stop_previous"
    assert PlaybackMode.STOP_SAME_SOUND.value == "stop_same_sound"
    assert PlaybackState.PLAYING.value == "playing"
