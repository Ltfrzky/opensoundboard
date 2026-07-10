# Architecture

`app.domain` contains Qt-free models, errors, enums, and replaceable contracts. `app.application`
coordinates those contracts. `app.infrastructure` provides SQLite, safe-file-library, Qt Multimedia,
and disabled-hotkey adapters. `app.presentation` contains PySide6 views and a thin view model.

Runtime data lives in the operating system's per-user application-data location: SQLite data,
managed media, and rotating logs are kept there rather than in the repository.
