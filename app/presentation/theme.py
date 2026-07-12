# ruff: noqa: E501
SIGNAL_CONSOLE_STYLESHEET = """
QMainWindow, QDialog { background: #080c12; color: #f3f7fb; font-family: Segoe UI, sans-serif; }
QFrame#boardRail, QFrame#playbackRail { background: #0b1118; border: 1px solid #263544; }
QFrame#capabilityBar { background: #0e171f; border: 1px solid #1d2a36; }
QFrame#operatorStrip { background: #0a1016; border-bottom: 1px solid #1d2a36; }
QFrame#operatorSeparator { background: #1d2a36; border: none; }
QFrame#soundCard { background: #101720; border: 1px solid #263544; border-radius: 9px; }
QFrame#soundCard[active="true"] { background: #0f222c; border: 2px solid #38d8ff; }
QFrame#soundCard[missing="true"] { background: #18150f; border: 1px solid #6a502c; }
QFrame[cssRole="soundPad"] {
    background: #101720; border: 1px solid #263544; border-radius: 10px;
}
QFrame[cssRole="soundPad"][active="true"] {
    background: #0f222c; border: 2px solid #38d8ff;
}
QFrame[cssRole="soundPad"][missing="true"] {
    background: #18150f; border: 1px solid #6a502c;
}
QFrame[cssRole="soundPad"][arranging="true"] { background: #141923; border-color: #486476; }
QLabel#eyebrow { color: #718594; font-size: 11px; font-weight: 700; }
QLabel#title { font-size: 24px; font-weight: 700; color: #f3f7fb; }
QLabel#muted, QLabel#fileLabel, QLabel#capabilityLabel { color: #91a1b2; font-size: 12px; }
QLabel#hotkeyLabel { color: #38d8ff; font-size: 11px; font-weight: 600; }
QLabel#padCount { color: #91a1b2; font-size: 12px; font-weight: 600; }
QPushButton[cssRole="hotkeyKeycap"] {
    min-width: 34px; color: #38d8ff; background: #0b151d; border: 1px solid #2a5364;
    border-radius: 5px; padding: 4px 8px; font-family: Consolas, monospace; font-size: 10px;
    font-weight: 700;
}
QLabel[cssRole="padControlLabel"] { color: #718594; font-size: 11px; font-weight: 700; }
QLabel[cssRole="padVolumeValue"] {
    color: #b7c4ce; font-family: Consolas, monospace; font-size: 11px; font-weight: 600;
}
QLabel[cssRole="padMissing"] { color: #f4b84a; font-size: 11px; font-weight: 700; }
QLabel#warningLabel { color: #f4b84a; font-size: 10px; font-weight: 700; }
QLabel#operatorLabel { color: #91a1b2; font-size: 11px; font-weight: 600; }
QLabel#volumeIcon { color: #dfe9ef; font-size: 12px; }
QLabel#masterVolumeValue { color: #b7c4ce; font-family: Consolas, monospace; font-size: 12px; }
QListWidget { background: transparent; border: none; color: #91a1b2; outline: 0; }
QListWidget::item { min-height: 30px; padding: 8px 7px; border-radius: 4px; }
QListWidget::item:selected { background: #0d2731; color: #f3f7fb; border-left: 2px solid #38d8ff; }
QListWidget:focus { border: 1px solid #38d8ff; border-radius: 5px; }
QPushButton { background: #17232e; color: #dfe9ef; border: 1px solid #2a3b4a; border-radius: 6px; padding: 7px 10px; font-size: 12px; font-weight: 600; }
QPushButton:hover { background: #1b2a37; border-color: #486476; }
QPushButton:pressed { background: #101923; border-color: #5d788a; }
QPushButton:focus, QComboBox:focus, QSlider:focus { border-color: #38d8ff; }
QPushButton#primaryButton, QPushButton#playButton { background: #38d8ff; color: #061117; border-color: #38d8ff; }
QPushButton#dangerButton { background: #3a1e24; color: #ffdfe2; border-color: #6d2c35; }
QPushButton#manageButton { min-width: 112px; color: #b7c4ce; background: #101820; }
QPushButton#manageButton[managing="true"] {
    color: #38d8ff; background: #0d2731; border-color: #2498b5;
}
QPushButton[cssRole="padDelete"] {
    min-width: 78px; background: #3a1e24; color: #ffdfe2; border-color: #6d2c35;
}
QPushButton[cssRole="padDelete"]:hover { background: #491920; border-color: #ff626b; }
QToolButton[cssRole="padActions"] {
    background: #101820; border: 1px solid #2a3b4a; border-radius: 6px; padding: 6px;
}
QToolButton[cssRole="padActions"]:hover { background: #1b2a37; border-color: #486476; }
QToolButton[cssRole="padActions"]:focus { border-color: #38d8ff; }
QPushButton[cssRole="padRecover"] {
    color: #f4b84a; background: transparent; border-color: #6a502c;
}
QPushButton#panicStopButton {
    background: #211116; color: #ff626b; border: 1px solid #ff3945; border-radius: 6px;
    min-height: 40px; padding: 2px 12px; font-size: 10px; font-weight: 700;
}
QPushButton#panicStopButton:hover { background: #32151b; color: #ff8087; border-color: #ff626b; }
QPushButton#panicStopButton:pressed { background: #491920; color: #ffffff; border-color: #ff8087; }
QPushButton#newBoardButton {
    color: #38d8ff; background: transparent; border: 1px solid #147a99;
    border-radius: 5px; font-size: 11px;
}
QPushButton#newBoardButton:hover { background: #0d2731; border-color: #38d8ff; }
QPushButton#newBoardButton:pressed { background: #102b36; }
QPushButton#settingsButton {
    color: #b7c4ce; background: transparent; border: none; border-top: 1px solid #1d2a36;
    border-radius: 0; padding-left: 4px; text-align: left;
}
QPushButton#settingsButton:hover { color: #f3f7fb; background: #101820; }
QPushButton#hotkeyToggleButton {
    min-height: 40px; border-radius: 5px; background: #101820; color: #91a1b2;
    border: 1px solid #2a3946; padding: 6px 10px; font-size: 10px; font-weight: 600;
}
QPushButton#hotkeyToggleButton:focus { border-color: #5d788a; }
QPushButton#hotkeyToggleButton[hotkeyState="on"] {
    background: #0d2731; color: #38d8ff; border-color: #2498b5;
}
QPushButton#hotkeyToggleButton[hotkeyState="on"]:focus { border-color: #38d8ff; }
QPushButton[cssRole="playbackModeButton"] {
    min-height: 40px; background: #101820; color: #b7c4ce; border: 1px solid #2a3946;
    border-radius: 0px; padding: 6px 8px; font-size: 10px; font-weight: 600;
}
QPushButton[cssRole="playbackModeButton"][segmentPosition="first"] {
    border-top-left-radius: 5px; border-bottom-left-radius: 5px;
}
QPushButton[cssRole="playbackModeButton"][segmentPosition="middle"] { margin-left: -1px; }
QPushButton[cssRole="playbackModeButton"][segmentPosition="last"] {
    margin-left: -1px; border-top-right-radius: 5px; border-bottom-right-radius: 5px;
}
QPushButton[cssRole="playbackModeButton"]:hover { background: #16232d; color: #f3f7fb; }
QPushButton[cssRole="playbackModeButton"]:checked {
    background: #0d2731; color: #38d8ff; border-color: #2498b5;
}
QToolButton#importButton {
    min-height: 40px; background: #101820; color: #f3f7fb; border: 1px solid #2a3946;
    border-radius: 5px; padding: 6px 28px 6px 12px; font-size: 11px; font-weight: 600;
}
QToolButton#importButton:hover { background: #16232d; border-color: #486476; }
QToolButton#importButton:pressed { background: #0d151d; border-color: #5d788a; }
QToolButton[cssRole="padTrigger"] {
    color: #f3f7fb; background: #111b24; border: 1px solid #2f4b5b; border-radius: 7px;
    min-width: 0; font-size: 14px; font-weight: 700; padding: 8px;
}
QToolButton[cssRole="padTrigger"]:hover { background: #132431; border-color: #486476; }
QToolButton[cssRole="padTrigger"]:pressed { background: #0d2731; border-color: #38d8ff; }
QToolButton[cssRole="padTrigger"]:focus { border-color: #38d8ff; }
QToolButton[cssRole="padTrigger"]:disabled { color: #8b7a5b; background: transparent; }
QToolButton#importButton::menu-button {
    width: 22px; border-left: 1px solid #2a3946; border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
}
QMenu { background: #101820; color: #dfe9ef; border: 1px solid #2a3946; padding: 4px; }
QMenu::item { min-height: 28px; padding: 4px 22px 4px 10px; border-radius: 4px; }
QMenu::item:selected { background: #0d2731; color: #38d8ff; }
QPushButton#linkButton { background: transparent; color: #38d8ff; border: none; }
QPushButton#recoverButton { background: transparent; color: #f4b84a; border: none; padding: 2px; }
QPushButton:disabled { color: #6d7882; background: #172028; border-color: #25313a; }
QComboBox, QSpinBox, QLineEdit { background: #121c26; color: #f3f7fb; border: 1px solid #2b3b48; border-radius: 6px; padding: 6px; }
QSlider::groove:horizontal { height: 5px; background: #263544; border-radius: 2px; }
QSlider::sub-page:horizontal { background: #38d8ff; border-radius: 2px; }
QSlider::handle:horizontal { background: #38d8ff; width: 14px; margin: -5px 0; border-radius: 7px; }
QSlider[cssRole="padVolume"]::groove:horizontal {
    height: 7px; background: #263544; border-radius: 4px;
}
QSlider[cssRole="padVolume"]::sub-page:horizontal { background: #38d8ff; border-radius: 4px; }
QSlider[cssRole="padVolume"]::handle:horizontal {
    width: 14px; margin: -4px 0; border-radius: 7px;
}
QPushButton[cssRole="padLoop"] {
    color: #b7c4ce; background: #101820; border-color: #2a3946; padding: 5px 10px;
}
QPushButton[cssRole="padLoop"]:checked {
    color: #061117; background: #38d8ff; border-color: #38d8ff;
}
QProgressBar { border: 0; background: #203542; height: 4px; border-radius: 2px; }
QProgressBar::chunk { background: #38d8ff; border-radius: 2px; }
QFrame[cssRole="playbackLane"] {
    background: #0e151d; border: 1px solid #263544; border-left: 3px solid #38d8ff;
    border-radius: 4px;
}
QFrame[cssRole="playbackLane"] QLabel { color: #f3f7fb; font-size: 11px; font-weight: 600; }
QLabel[cssRole="playbackTime"] {
    color: #38d8ff; font-family: Consolas, monospace; font-size: 10px;
}
QLabel#laneCountLabel, QLabel#hotkeyStatusHeading { color: #91a1b2; font-size: 10px; }
QLabel#playbackEmptyLabel, QLabel#hotkeyEmptyLabel { color: #718594; font-size: 11px; }
QFrame#hotkeyPanel { border-top: 1px solid #1d2a36; }
QLabel#hotkeyStateLabel { color: #f4b84a; font-size: 15px; font-weight: 700; }
QLabel#hotkeyStateLabel[state="ready"] { color: #54db7a; }
QLabel#hotkeyDetailLabel { color: #91a1b2; font-size: 12px; }
QLabel[cssRole="hotkeyRow"] {
    color: #b7c4ce; font-family: Consolas, monospace; font-size: 10px; padding: 3px 0;
}
QListWidget#settingsCategories { background: #0a1016; border-right: 1px solid #1d2a36; }
QListWidget#settingsCategories::item { min-height: 28px; }
QLabel#settingsPageTitle { color: #f3f7fb; font-size: 16px; font-weight: 700; }
QLabel#hotkeyDebounceLabel, QLabel#panicShortcutHeading {
    color: #b7c4ce; font-size: 12px; font-weight: 600;
}
QLabel#generalSettingsInfo { color: #91a1b2; font-size: 12px; }
QScrollArea { border: none; background: #0c1219; }
QScrollArea QWidget#cueContent, QScrollArea QWidget#qt_scrollarea_viewport { background: #0c1219; }
QMessageBox { background: #101820; }
"""
