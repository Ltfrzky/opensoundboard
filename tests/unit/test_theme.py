from app.presentation.theme import SIGNAL_CONSOLE_STYLESHEET


def test_hotkey_toggle_uses_a_single_border_for_checked_and_focused_states() -> None:
    assert (
        "QPushButton:focus, QComboBox:focus, QSlider:focus { outline:"
        not in SIGNAL_CONSOLE_STYLESHEET
    )
    assert 'QPushButton#hotkeyToggleButton:focus' in SIGNAL_CONSOLE_STYLESHEET
    assert 'QListWidget:focus' in SIGNAL_CONSOLE_STYLESHEET


def test_sound_pad_theme_defines_pad_keycap_arrange_and_inline_control_states() -> None:
    selectors = (
        'QFrame[cssRole="soundPad"]',
        'QFrame[cssRole="soundPad"][active="true"]',
        'QFrame[cssRole="soundPad"][missing="true"]',
        'QPushButton[cssRole="hotkeyKeycap"]',
        'QPushButton#manageButton[managing="true"]',
        'QPushButton[cssRole="padDelete"]',
        'QToolButton[cssRole="padActions"]',
        'QToolButton[cssRole="padTrigger"]',
        'QSlider[cssRole="padVolume"]',
        'QLabel[cssRole="padVolumeValue"]',
        'QPushButton[cssRole="padLoop"]',
    )

    for selector in selectors:
        assert selector in SIGNAL_CONSOLE_STYLESHEET

    assert 'QSlider[cssRole="padVolume"]::groove:horizontal' in SIGNAL_CONSOLE_STYLESHEET
    assert 'height: 7px; background: #263544; border-radius: 4px;' in SIGNAL_CONSOLE_STYLESHEET
    assert 'border-radius: 4px;' in SIGNAL_CONSOLE_STYLESHEET


def test_rail_theme_defines_reference_faithful_navigation_and_status_states() -> None:
    selectors = (
        'QPushButton#newBoardButton',
        'QPushButton#settingsButton',
        'QFrame[cssRole="playbackLane"]',
        'QLabel#hotkeyStateLabel[state="ready"]',
        'QLabel[cssRole="hotkeyRow"]',
        'QListWidget#settingsCategories',
        'QLabel#settingsPageTitle',
    )

    for selector in selectors:
        assert selector in SIGNAL_CONSOLE_STYLESHEET
