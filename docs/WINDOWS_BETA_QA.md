# Windows Beta QA Gate

Run this gate before distributing a Windows beta, and run the packaged-artifact smoke pass
after extracting the portable ZIP. This gate is required in addition to the automated suite.

## Preparation and evidence

1. Use a dedicated Windows test account with an unused OpenSoundboard AppData profile. Do not
   delete or edit a regular user's database, managed media, or logs.
2. Create an untracked local `qa-media/` directory with one valid 2--10 second clip for each
   supported extension: `.wav`, `.mp3`, `.ogg`, `.flac`, and `.m4a`. Do not add these files to Git.
3. Record the Git commit, OpenSoundboard version, Windows version, audio output device, tester,
   date, and the global-hotkey capability state shown by the application.
4. Run the automated gate:

   ```powershell
   .venv\Scripts\ruff check .
   .venv\Scripts\python -m pytest
   ```

## Source-tree acceptance pass

- Import each media-pack clip by managed copy; confirm every sound card is enabled and plays audibly.
- Import one clip by source reference; restart, then confirm it remains playable. Re-import that
  source and confirm duplicate feedback appears without a second sound entry.
- Move the referenced source file, restart, confirm the card is disabled, then recover it with a
  replacement file and confirm it plays again.
- Create, rename, and delete an empty board. Verify deletion of a non-empty board is rejected.
  Rename, move, and delete a sound while it is playing; confirm its lane stops before removal.
- Verify overlap creates independent lanes, stop previous stops the earlier lane, stop same sound
  stops only that sound, loop repeats, master and per-sound volume affect audible output, individual
  lane stop works, and Stop All clears every lane.
- Restart and confirm boards, sounds, playback mode, volumes, loop state, and assignments persist.
- Enable global hotkeys, assign a sound shortcut and Panic Stop, confirm duplicate assignment needs
  explicit replacement, and confirm each shortcut fires while another application has focus. Trigger
  the sound shortcut rapidly and confirm the configured debounce prevents repeated playback.

## Packaged-artifact smoke pass

1. Build the archive with `scripts\build_windows.ps1` as documented in `PACKAGING.md`.
2. Extract the ZIP to a new folder; never launch the executable from inside the archive.
3. Launch `OpenSoundboard\OpenSoundboard.exe`, import and audibly play the WAV and MP3 samples,
   assign and trigger one global hotkey outside the app, use Stop All, then restart and confirm
   persistence.
4. Mark the beta passed only when every automated and manual case passes. Triage every failure;
   any reproducible non-hardware defect needs a regression test and fix before rerunning this gate.
