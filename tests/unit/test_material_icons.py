import importlib.util

import pytest
from PySide6.QtWidgets import QApplication


def test_material_icon_helper_is_available() -> None:
    assert importlib.util.find_spec("app.presentation.material_icons") is not None


def test_material_icon_helper_renders_registered_icons_and_rejects_unknown_names() -> None:
    QApplication.instance() or QApplication([])
    from app.presentation.material_icons import MATERIAL_ICON_NAMES, material_icon

    assert {"apps", "file_upload", "mic"}.issubset(MATERIAL_ICON_NAMES)
    assert not material_icon("file_upload", size=16, off_color="#dfe9ef").isNull()
    assert not material_icon("mic", size=16, off_color="#dfe9ef").isNull()
    with pytest.raises(ValueError, match="Unknown Material icon"):
        material_icon("not_an_icon", size=16, off_color="#dfe9ef")
