import os
from pathlib import Path

from app.infrastructure.file_library import FileLibrary


def test_normalized_path_uses_the_current_platform_case_rules(tmp_path: Path) -> None:
    path = tmp_path / "A.wav"
    path.write_bytes(b"RIFF")

    assert FileLibrary.normalized(path) == os.path.normcase(str(path.resolve()))
