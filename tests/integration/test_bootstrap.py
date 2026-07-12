import logging
from pathlib import Path

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFrame,
    QLabel,
    QPushButton,
    QSlider,
    QToolButton,
    QWidget,
)

from app.application.hotkeys import HotkeyCoordinator
from app.bootstrap import create_context
from app.domain.enums.hotkey_status import HotkeyStatusState
from app.domain.enums.playback import PlaybackMode
from app.domain.interfaces import HotkeyStatus
from app.domain.models import PlaybackSnapshot, Sound
from app.presentation.board_settings import BoardSettingsDialog
from app.presentation.main_window import MainWindow
from app.presentation.settings_dialog import SettingsDialog
from app.presentation.sound_pad import SoundPad


def test_bootstrap_creates_a_window_with_default_board(tmp_path: Path) -> None:
    application = QApplication.instance() or QApplication([])
    context = create_context(tmp_path)
    window = MainWindow(context.service, context.hotkeys)

    assert window.windowTitle() == "OpenSoundboard"
    assert window.board_list.count() == 1
    window.close()
    application.processEvents()


def test_injected_data_path_does_not_install_a_global_file_handler(tmp_path: Path) -> None:
    create_context(tmp_path)

    handlers = logging.getLogger("opensoundboard").handlers

    assert not [handler for handler in handlers if getattr(handler, "baseFilename", "")]


def test_sound_pad_uses_supported_slider_release_signal(tmp_path: Path) -> None:
    application = QApplication.instance() or QApplication([])
    context = create_context(tmp_path)
    window = MainWindow(context.service, context.hotkeys)
    board = context.service.list_boards()[0]
    sound_path = tmp_path / "test.wav"
    sound_path.write_bytes(b"RIFF")
    sound = context.service.sounds.save_sound(
        Sound(0, board.id, "Test", sound_path)
    )

    pad = window._sound_pad(sound)

    assert pad is not None
    volume = pad.findChild(QSlider, f"padVolume-{sound.id}")
    assert volume is not None
    volume.setValue(42)
    volume.sliderReleased.emit()
    assert context.service.get_sound(sound.id).volume == 42
    window.close()
    application.processEvents()


def test_board_settings_persists_the_selected_material_icon(tmp_path: Path) -> None:
    application = QApplication.instance() or QApplication([])
    context = create_context(tmp_path)
    board = context.service.list_boards()[0]
    dialog = BoardSettingsDialog(context.service, board)

    assert not dialog.icon_selector.itemIcon(0).isNull()
    dialog.name_input.setText("Podcast")
    dialog.icon_selector.setCurrentText("mic")
    dialog.save()

    assert context.service.list_boards()[0].name == "Podcast"
    assert context.service.list_boards()[0].icon == "mic"
    dialog.close()
    application.processEvents()


def test_settings_dialog_exposes_general_and_hotkey_pages(tmp_path: Path) -> None:
    application = QApplication.instance() or QApplication([])
    context = create_context(tmp_path)
    dialog = SettingsDialog(context.service, HotkeyCoordinator(context.service, context.hotkeys))

    assert [dialog.category_list.item(index).text() for index in range(2)] == [
        "General",
        "Hotkeys",
    ]
    assert "Library location" in dialog.general_page_text.text()
    assert dialog.hotkey_page.findChild(QPushButton, "reRegisterHotkeysButton") is not None
    dialog.close()
    application.processEvents()


def test_sound_pad_displays_the_assigned_hotkey_once_and_hides_delete_normally(
    tmp_path: Path,
) -> None:
    application = QApplication.instance() or QApplication([])
    sound_path = tmp_path / "airhorn.wav"
    sound_path.write_bytes(b"RIFF")
    sound = Sound(7, 1, "Airhorn", sound_path, hotkey="Ctrl+1")

    pad = SoundPad(sound, active=False, arrange_mode=False)

    hotkey = pad.findChild(QPushButton, "padHotkey-7")
    delete = pad.findChild(QPushButton, "padDelete-7")
    trigger = pad.findChild(QToolButton, "padTrigger-7")
    assert hotkey is not None and hotkey.text() == "Ctrl + 1"
    assert delete is not None and delete.isHidden()
    assert trigger is not None and trigger.isEnabled()
    assert not pad.findChildren(QLabel, "soundKind-7")
    pad.close()
    application.processEvents()


def test_sound_pad_uses_full_width_trigger_loop_button_and_clickable_hotkey(
    tmp_path: Path,
) -> None:
    application = QApplication.instance() or QApplication([])
    sound_path = tmp_path / "bonk.wav"
    sound_path.write_bytes(b"RIFF")
    sound = Sound(10, 1, "Bonk", sound_path, hotkey="Ctrl+3")

    pad = SoundPad(sound, active=False, arrange_mode=False)
    trigger = pad.findChild(QToolButton, "padTrigger-10")
    loop = pad.findChild(QPushButton, "padLoop-10")
    hotkey = pad.findChild(QPushButton, "padHotkey-10")
    hotkey_spy = QSignalSpy(pad.hotkey_requested)

    assert trigger is not None
    assert trigger.sizePolicy().horizontalPolicy().name == "Expanding"
    assert loop is not None and loop.isCheckable()
    assert hotkey is not None and hotkey.isEnabled()
    assert not pad.findChildren(QCheckBox)
    hotkey.click()
    assert hotkey_spy.count() == 1
    assert hotkey_spy.at(0) == [10]
    pad.close()
    application.processEvents()


def test_sound_pad_arrange_mode_reveals_delete_and_disables_playback() -> None:
    application = QApplication.instance() or QApplication([])
    sound = Sound(8, 1, "Transition", Path("transition.wav"))

    pad = SoundPad(sound, active=False, arrange_mode=True)

    delete = pad.findChild(QPushButton, "padDelete-8")
    trigger = pad.findChild(QToolButton, "padTrigger-8")
    assert delete is not None and not delete.isHidden()
    assert trigger is not None and not trigger.isEnabled()
    pad.close()
    application.processEvents()


def test_sound_pad_context_menu_keeps_sound_management_actions() -> None:
    application = QApplication.instance() or QApplication([])
    sound = Sound(9, 1, "Stinger", Path("stinger.wav"), hotkey="Ctrl+2")

    pad = SoundPad(sound, active=False, arrange_mode=False)

    assert [action.text() for action in pad.context_menu().actions()] == [
        "Rename",
        "Change hotkey",
        "Clear hotkey",
        "Move to board…",
    ]
    pad.close()
    application.processEvents()


def test_sound_pad_exposes_a_visible_actions_menu() -> None:
    application = QApplication.instance() or QApplication([])
    sound = Sound(12, 1, "Stinger", Path("stinger.wav"), hotkey="Ctrl+2")

    pad = SoundPad(sound, active=False, arrange_mode=False)
    actions = pad.findChild(QToolButton, "padActions-12")

    assert actions is not None
    assert actions.minimumWidth() >= 40
    assert actions.minimumHeight() >= 40
    assert actions.accessibleName() == "Manage Stinger"
    actions_text = [action.text() for action in actions.menu().actions()]
    assert actions_text[:3] == ["Rename", "Change hotkey", "Clear hotkey"]
    assert actions_text[3].startswith("Move to board")
    pad.close()
    application.processEvents()


def test_cue_workspace_uses_four_column_pads_and_arrange_mode(tmp_path: Path) -> None:
    application = QApplication.instance() or QApplication([])
    context = create_context(tmp_path)
    board = context.service.list_boards()[0]
    sounds = []
    for index in range(5):
        sound_path = tmp_path / f"cue-{index}.wav"
        sound_path.write_bytes(b"RIFF")
        sounds.append(
            context.service.sounds.save_sound(Sound(0, board.id, f"Cue {index}", sound_path))
        )
    window = MainWindow(context.service, context.hotkeys)
    window.refresh_sounds(0)

    assert window._grid.columnCount() == 4
    assert window._grid.itemAtPosition(0, 3) is not None
    assert window._grid.itemAtPosition(1, 0) is not None
    manage = window.findChild(QPushButton, "manageButton")
    assert manage is not None
    assert manage.text() == "Manage sounds"
    assert manage.toolTip() == "Show sound deletion controls"
    manage.click()
    application.processEvents()

    pad = window._grid.itemAtPosition(0, 0).widget()
    delete = pad.findChild(QPushButton, f"padDelete-{sounds[0].id}")
    trigger = pad.findChild(QToolButton, f"padTrigger-{sounds[0].id}")
    assert delete is not None and not delete.isHidden()
    assert trigger is not None and not trigger.isEnabled()
    assert manage.text() == "Done"
    assert manage.toolTip() == "Hide sound deletion controls"
    window.close()
    application.processEvents()


def test_signal_console_exposes_collapsed_activity_rail_and_capability_link(tmp_path: Path) -> None:
    application = QApplication.instance() or QApplication([])
    context = create_context(tmp_path)
    window = MainWindow(context.service, context.hotkeys)
    window.show()
    application.processEvents()

    activity_rail = window.findChild(QWidget, "activityRail")
    activity_toggle = window.findChild(QPushButton, "activityToggleButton")
    assert activity_rail is not None and activity_rail.isHidden()
    assert activity_toggle is not None and activity_toggle.text() == "Activity (0)"
    capability_button = window.findChild(QPushButton, "capabilityButton")
    assert capability_button is not None
    assert not capability_button.icon().isNull()
    assert window.findChild(QPushButton, "panicStopButton") is not None
    hotkey_toggle = window.findChild(QPushButton, "hotkeyToggleButton")
    assert hotkey_toggle is not None
    assert hotkey_toggle.text() == "Hotkeys Off"

    hotkey_toggle.click()

    assert context.service.settings.get_setting("hotkeys_enabled", "0") == "1"
    assert hotkey_toggle.text() == "Hotkeys On"

    window.close()
    application.processEvents()


def test_rail_layout_exposes_icon_boards_settings_and_capability_status(tmp_path: Path) -> None:
    application = QApplication.instance() or QApplication([])
    context = create_context(tmp_path)
    window = MainWindow(context.service, context.hotkeys)
    window.refresh_boards()
    window._refresh_capability()

    assert window.findChild(QWidget, "boardRail").minimumWidth() == 170
    assert not window.board_list.item(0).icon().isNull()
    board_settings = window.findChild(QPushButton, "boardSettingsButton")
    assert board_settings is not None
    assert board_settings.text() == "Edit board"
    assert board_settings.toolTip() == "Board settings"
    assert window.findChild(QPushButton, "settingsButton") is not None
    assert window.findChild(QWidget, "hotkeyPanel") is None
    capability = window.findChild(QLabel, "capabilityLabel")
    assert capability is not None and "Global hotkeys" in capability.text()

    window.close()
    application.processEvents()


def test_active_playback_rail_renders_compact_lane_and_stops_it(tmp_path: Path) -> None:
    application = QApplication.instance() or QApplication([])
    context = create_context(tmp_path)
    board = context.service.list_boards()[0]
    source = tmp_path / "intro.wav"
    source.write_bytes(b"RIFF")
    sound = context.service.sounds.save_sound(Sound(0, board.id, "Intro", source))
    window = MainWindow(context.service, context.hotkeys)
    window.show()
    application.processEvents()
    window._active_lanes = [PlaybackSnapshot("lane-1", sound.id, 4_000, 12_000)]
    window._refresh_lanes()

    activity_rail = window.findChild(QWidget, "activityRail")
    assert activity_rail is not None and not activity_rail.isHidden()
    lane = window.findChild(QFrame, "playbackLane-lane-1")
    timer = window.findChild(QLabel, "playbackTime-lane-1")
    stop = window.findChild(QPushButton, "stopLane-lane-1")
    assert lane is not None
    assert timer is not None and timer.text() == "00:04 / 00:12"
    assert stop is not None and stop.minimumHeight() >= 40
    stopped: list[str] = []
    window.stop_lane = stopped.append
    stop.click()

    assert stopped == ["lane-1"]
    window.close()
    application.processEvents()


def test_capability_bar_preserves_permission_required_state(tmp_path: Path) -> None:
    application = QApplication.instance() or QApplication([])
    context = create_context(tmp_path)
    window = MainWindow(context.service, context.hotkeys)
    status = HotkeyStatus(
        HotkeyStatusState.MACOS_PERMISSION_REQUIRED,
        True,
        "macOS permission may be required",
        "Grant Accessibility permission to use global hotkeys.",
    )

    window.coordinator.status = lambda: status
    window._refresh_capability()

    capability = window.findChild(QLabel, "capabilityLabel")
    assert capability is not None
    assert "macOS permission may be required" in capability.text()
    assert "Grant Accessibility permission" in capability.text()
    window.close()
    application.processEvents()


def test_activity_rail_can_be_pinned_while_idle_and_auto_expands_for_playback(
    tmp_path: Path,
) -> None:
    application = QApplication.instance() or QApplication([])
    context = create_context(tmp_path)
    board = context.service.list_boards()[0]
    source = tmp_path / "activity.wav"
    source.write_bytes(b"RIFF")
    sound = context.service.sounds.save_sound(Sound(0, board.id, "Activity", source))
    window = MainWindow(context.service, context.hotkeys)
    window.show()
    application.processEvents()
    activity_rail = window.findChild(QWidget, "activityRail")
    activity_toggle = window.findChild(QPushButton, "activityToggleButton")

    assert activity_rail is not None and activity_rail.isHidden()
    assert activity_toggle is not None
    activity_toggle.click()
    assert not activity_rail.isHidden()
    activity_toggle.click()
    assert activity_rail.isHidden()

    window._active_lanes = [PlaybackSnapshot("lane-1", sound.id, 1_000, 2_000)]
    window._refresh_lanes()
    assert not activity_rail.isHidden()

    window._active_lanes = []
    window._refresh_lanes()
    assert activity_rail.isHidden()
    window.close()
    application.processEvents()


def test_operator_strip_is_the_single_global_home_for_transport_controls(tmp_path: Path) -> None:
    application = QApplication.instance() or QApplication([])
    context = create_context(tmp_path)
    window = MainWindow(context.service, context.hotkeys)

    operator_strip = window.findChild(QFrame, "operatorStrip")

    assert operator_strip is not None
    assert window.centralWidget().layout().itemAt(0).widget() is operator_strip
    assert operator_strip.findChild(QPushButton, "panicStopButton") is not None
    assert len(window.findChildren(QPushButton, "panicStopButton")) == 1
    assert operator_strip.findChild(QPushButton, "playbackModeOverlapButton") is not None
    assert operator_strip.findChild(QPushButton, "playbackModeStopPreviousButton") is not None
    assert operator_strip.findChild(QPushButton, "playbackModeStopSameButton") is not None

    window.close()
    application.processEvents()


def test_operator_strip_split_import_emits_managed_and_reference_choices(tmp_path: Path) -> None:
    application = QApplication.instance() or QApplication([])
    context = create_context(tmp_path)
    window = MainWindow(context.service, context.hotkeys)
    operator_strip = getattr(window, "operator_strip", None)

    assert operator_strip is not None
    operator_strip.import_requested.disconnect(window.import_files)
    spy = QSignalSpy(operator_strip.import_requested)
    import_button = operator_strip.findChild(QToolButton, "importButton")
    assert import_button is not None

    import_button.click()
    reference_action = next(
        action
        for action in import_button.menu().actions()
        if action.text() == "Reference originals"
    )
    reference_action.trigger()

    assert spy.count() == 2
    assert spy.at(0) == [True]
    assert spy.at(1) == [False]
    window.close()
    application.processEvents()


def test_operator_strip_shows_a_labelled_import_control_at_normal_width(tmp_path: Path) -> None:
    application = QApplication.instance() or QApplication([])
    context = create_context(tmp_path)
    window = MainWindow(context.service, context.hotkeys)
    import_button = window.operator_strip.findChild(QToolButton, "importButton")

    assert import_button is not None
    assert import_button.text() == "Import audio"
    assert import_button.toolButtonStyle() is Qt.ToolButtonStyle.ToolButtonTextBesideIcon

    window.close()
    application.processEvents()


def test_header_import_requests_managed_copy(tmp_path: Path) -> None:
    application = QApplication.instance() or QApplication([])
    context = create_context(tmp_path)
    window = MainWindow(context.service, context.hotkeys)
    requests: list[bool | None] = []
    window.import_files = requests.append

    window._request_managed_import()

    assert requests == [True]
    window.close()
    application.processEvents()


def test_operator_strip_routes_volume_and_all_playback_modes(tmp_path: Path) -> None:
    application = QApplication.instance() or QApplication([])
    context = create_context(tmp_path)
    window = MainWindow(context.service, context.hotkeys)
    operator_strip = getattr(window, "operator_strip", None)

    assert operator_strip is not None
    slider = operator_strip.findChild(QSlider, "masterVolumeSlider")
    volume_label = operator_strip.findChild(QLabel, "masterVolumeValue")
    assert slider is not None
    assert volume_label is not None

    slider.setValue(42)
    assert context.service.master_volume() == 42
    assert volume_label.text() == "42%"

    cases = (
        ("playbackModeOverlapButton", PlaybackMode.OVERLAP),
        ("playbackModeStopPreviousButton", PlaybackMode.STOP_PREVIOUS),
        ("playbackModeStopSameButton", PlaybackMode.STOP_SAME_SOUND),
    )
    for object_name, expected_mode in cases:
        button = operator_strip.findChild(QPushButton, object_name)
        assert button is not None
        assert button.toolTip()
        button.click()
        assert context.service.playback_mode() is expected_mode

    window.close()
    application.processEvents()


def test_operator_strip_uses_hotkey_toggle_and_panic_control_without_live_status(
    tmp_path: Path,
) -> None:
    application = QApplication.instance() or QApplication([])
    context = create_context(tmp_path)
    context.service.settings.set_setting("panic_stop_hotkey", "Ctrl+Shift+P")
    window = MainWindow(context.service, context.hotkeys)
    operator_strip = getattr(window, "operator_strip", None)

    assert operator_strip is not None
    live_status = operator_strip.findChild(QLabel, "liveStatusLabel")
    hotkey_toggle = operator_strip.findChild(QPushButton, "hotkeyToggleButton")
    panic = operator_strip.findChild(QPushButton, "panicStopButton")
    assert live_status is None
    assert hotkey_toggle is not None
    assert panic is not None
    assert hotkey_toggle.text() == "Hotkeys Off"
    assert hotkey_toggle.toolTip() == "Enable global hotkeys"
    assert hotkey_toggle.accessibleName() == "Enable global hotkeys"
    assert panic.text() == "PANIC STOP\nCtrl + Shift + P"
    assert not panic.icon().isNull()

    hotkey_toggle.click()

    assert hotkey_toggle.isChecked()
    assert hotkey_toggle.text() == "Hotkeys On"
    assert hotkey_toggle.toolTip() == "Disable global hotkeys"
    assert hotkey_toggle.accessibleName() == "Disable global hotkeys"
    window.close()
    application.processEvents()


def test_operator_strip_compacts_without_cropping_controls_at_minimum_width(tmp_path: Path) -> None:
    application = QApplication.instance() or QApplication([])
    context = create_context(tmp_path)
    window = MainWindow(context.service, context.hotkeys)
    window.resize(1000, 620)
    window.show()
    application.processEvents()

    operator_strip = window.operator_strip
    import_button = operator_strip.findChild(QToolButton, "importButton")
    hotkey_toggle = operator_strip.findChild(QPushButton, "hotkeyToggleButton")
    assert import_button is not None
    assert hotkey_toggle is not None
    assert import_button.toolButtonStyle() is Qt.ToolButtonStyle.ToolButtonIconOnly
    assert hotkey_toggle.text() == "Off"

    for control in operator_strip.findChildren(QPushButton):
        bounds = QRect(control.mapTo(operator_strip, QPoint(0, 0)), control.size())
        assert operator_strip.rect().contains(bounds)
        assert control.width() >= 40
        assert control.height() >= 40

    window.close()
    application.processEvents()


def test_missing_sound_pad_has_recovery_not_playback(tmp_path: Path) -> None:
    application = QApplication.instance() or QApplication([])
    context = create_context(tmp_path)
    board = context.service.list_boards()[0]
    sound = context.service.sounds.save_sound(Sound(0, board.id, "Missing", tmp_path / "gone.wav"))
    window = MainWindow(context.service, context.hotkeys)
    window.refresh_sounds(0)

    play = window.findChild(QToolButton, f"padTrigger-{sound.id}")
    recover = window.findChild(QPushButton, f"recoverButton-{sound.id}")

    assert play is not None and not play.isEnabled()
    assert recover is not None
    window.close()
    application.processEvents()


def test_overlap_retriggers_an_active_sound_instead_of_stopping_it(tmp_path: Path) -> None:
    application = QApplication.instance() or QApplication([])
    context = create_context(tmp_path)
    context.service.set_playback_mode(PlaybackMode.OVERLAP)
    window = MainWindow(context.service, context.hotkeys)
    sound_id = 42
    played: list[int] = []
    stopped: list[int] = []
    window._active_sound_ids = {sound_id}
    window._play = lambda requested_id: played.append(requested_id)
    window.service.stop = lambda requested_id: stopped.append(requested_id)

    MainWindow._toggle_sound(window, sound_id)

    assert played == [sound_id]
    assert stopped == []
    window.close()
    application.processEvents()


def test_playback_selector_persists_overlap_mode(tmp_path: Path) -> None:
    application = QApplication.instance() or QApplication([])
    context = create_context(tmp_path)
    window = MainWindow(context.service, context.hotkeys)

    overlap = window.findChild(QPushButton, "playbackModeOverlapButton")
    assert overlap is not None
    overlap.click()
    application.processEvents()

    assert context.service.playback_mode() is PlaybackMode.OVERLAP
    window.close()
    application.processEvents()


def test_playback_selector_exposes_stop_same_sound_mode(tmp_path: Path) -> None:
    application = QApplication.instance() or QApplication([])
    context = create_context(tmp_path)
    window = MainWindow(context.service, context.hotkeys)

    stop_same = window.findChild(QPushButton, "playbackModeStopSameButton")
    assert stop_same is not None
    stop_same.click()
    application.processEvents()

    assert context.service.playback_mode() is PlaybackMode.STOP_SAME_SOUND
    window.close()
    application.processEvents()
