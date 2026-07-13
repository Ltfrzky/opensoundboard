import os
from pathlib import Path

import pytest

from app.domain.errors import InvalidSoundError
from app.infrastructure.file_library import FileLibrary


def test_normalized_path_uses_the_current_platform_case_rules(tmp_path: Path) -> None:
    path = tmp_path / "A.wav"
    path.write_bytes(b"RIFF")

    assert FileLibrary.normalized(path) == os.path.normcase(str(path.resolve()))


@pytest.mark.parametrize("copy_file", [True, False])
def test_store_rejects_symlinked_audio_for_copy_and_reference(
    tmp_path: Path, copy_file: bool, monkeypatch
) -> None:
    source = tmp_path / "source.wav"
    source.write_bytes(b"RIFF")
    library = FileLibrary(tmp_path / "library")
    monkeypatch.setattr(Path, "is_symlink", lambda path: path == source)

    with pytest.raises(InvalidSoundError, match="symbolic links"):
        library.store(source, copy_file=copy_file)
