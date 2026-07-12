from __future__ import annotations

from pathlib import Path
from typing import Literal, cast

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

IconName = Literal[
    "add", "apps", "arrow_forward", "close", "cloud_done", "delete", "edit", "equalizer",
    "file_upload", "keyboard", "layers", "play_arrow", "repeat_one", "restore",
    "mic", "settings", "stop", "stop_circle", "volume_up", "warning_amber",
]

_ASSET_DIRECTORY = Path(__file__).parent / "assets" / "material-symbols"
MATERIAL_ICON_NAMES: tuple[IconName, ...] = (
    "add", "apps", "arrow_forward", "close", "cloud_done", "delete", "edit", "equalizer",
    "file_upload", "keyboard", "layers", "play_arrow", "repeat_one", "restore",
    "mic", "settings", "stop", "stop_circle", "volume_up", "warning_amber",
)


def material_icon(
    name: IconName | str,
    *,
    size: int = 16,
    off_color: str = "#dfe9ef",
    on_color: str | None = None,
) -> QIcon:
    """Render a bundled Material icon with optional checked-state coloring."""
    if name not in MATERIAL_ICON_NAMES:
        raise ValueError(f"Unknown Material icon: {name}")
    if size <= 0:
        raise ValueError("Material icon size must be positive")
    icon_name = cast(IconName, name)
    icon = QIcon()
    icon.addPixmap(_render(icon_name, size, off_color), QIcon.Mode.Normal, QIcon.State.Off)
    if on_color is not None:
        icon.addPixmap(_render(icon_name, size, on_color), QIcon.Mode.Normal, QIcon.State.On)
    return icon


def _render(name: IconName, size: int, color: str) -> QPixmap:
    svg = (_ASSET_DIRECTORY / f"{name}.svg").read_text(encoding="utf-8")
    renderer = QSvgRenderer(svg.replace("currentColor", QColor(color).name()).encode("utf-8"))
    if not renderer.isValid():
        raise ValueError(f"Invalid Material icon asset: {name}")
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap
