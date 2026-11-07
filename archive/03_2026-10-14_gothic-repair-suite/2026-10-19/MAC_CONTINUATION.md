# Continue the Gothic repair project on macOS

This bundle is a portable snapshot of the local repair suite and its artwork history. The current continuation image is:

`assets/current/Demiurge_Current_2048_2026-10-19.png`

- Dimensions: 2048×2048 RGB
- SHA-256: `3d6022dafe77d6a93fcf5dac1a6ac6f70b0a29ab2d7dca419c6b058a42f6764c`
- Role: current edit destination; preserve it and save new revisions under new filenames.

## First launch

1. Extract the ZIP into a normal writable folder such as `~/Documents/Gothic-Repair-Suite`.
2. Open Terminal and drag the extracted folder into the Terminal window after typing `cd `.
3. Run:

```bash
chmod +x setup_mac.sh launch_mac.sh run_tests_mac.sh
./setup_mac.sh
./launch_mac.sh
```

Python 3.10 or newer is required. The setup script creates a private `.venv`; it does not change the system Python. It works on Apple Silicon and Intel Macs using the wheels supplied by the Python packages.

## Verify the handoff

```bash
./run_tests_mac.sh
shasum -a 256 assets/current/Demiurge_Current_2048_2026-10-19.png
```

The image hash must match the value above. The project test suite verifies masking, persistence, undo/redo, exports, asset alignment, and headless UI startup.

## Continue the artwork

- Start from the current 2048 image, not an older v-numbered output.
- Read `docs/prompts/current-master-repair-instructions.md` before sending work to another image editor.
- Use separate masks for anatomy, demon claw, reclining figure, halos, cybernetics, and starfield/eclipses.
- Save each accepted pass under a new filename. Never overwrite the current image or any reference.
- Review at 100% and 400% zoom before accepting a candidate.
- Export an absolute-difference image and verify that no pixel outside the approved mask changed.

## Restore full Git history

The ZIP includes `Gothic_Repair_Suite_History.bundle`. To create a separate Git checkout with all bundled branches and commits:

```bash
cd ..
git clone Gothic_Repair_Suite_Mac/Gothic_Repair_Suite_History.bundle gothic-repair-suite-history
```

The extracted project itself is ready to run without Git. The bundle exists so development history can be restored if desired.

## Optional remote or local AI backend

The built-in OpenCV backend is useful for seams and texture propagation but cannot reliably invent complex anatomy. A stronger service can be connected through `GOTHIC_REPAIR_ENDPOINT` and optional `GOTHIC_REPAIR_TOKEN`, or through a trusted plugin based on `plugins/example_backend.py.example`. Never put API keys in the project files or ZIP.

## Important boundaries

- The included generative image attempts are historical evidence, not automatically approved artistic results.
- Automated QA proves pixel confinement and file integrity; it does not prove that anatomy is artistically correct.
- V12 was rejected because copper outlines did not read as real cybernetics. V13 contains actual mechanical overlay objects but still requires visual approval.
