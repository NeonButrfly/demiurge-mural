"""Create a verified portable macOS continuation ZIP from the tracked project."""
from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from datetime import date
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "Gothic_Repair_Suite_Mac"
OUTPUT = ROOT / "outputs" / f"Gothic_Repair_Suite_Mac_Continuation_{date.today().isoformat()}.zip"
CURRENT = Path("assets/current/Demiurge_Current_2048_2026-10-19.png")


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    tracked = [Path(line) for line in run("git", "ls-files").splitlines() if line]
    required = {
        Path("MAC_CONTINUATION.md"),
        Path("setup_mac.sh"),
        Path("launch_mac.sh"),
        Path("run_tests_mac.sh"),
        Path("docs/prompts/current-master-repair-instructions.md"),
        CURRENT,
    }
    missing = sorted(str(path) for path in required if path not in tracked or not (ROOT / path).is_file())
    if missing:
        raise SystemExit(f"Required tracked files missing: {missing}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="gothic-mac-bundle-") as folder:
        history = Path(folder) / "Gothic_Repair_Suite_History.bundle"
        subprocess.check_call(["git", "bundle", "create", str(history), "--all"], cwd=ROOT)
        entries: dict[str, bytes] = {}
        for relative in tracked:
            path = ROOT / relative
            if path.is_file():
                entries[relative.as_posix()] = path.read_bytes()
        entries[history.name] = history.read_bytes()

        info = {
            "created": date.today().isoformat(),
            "source_commit": run("git", "rev-parse", "HEAD"),
            "source_branch": run("git", "branch", "--show-current"),
            "current_image": CURRENT.as_posix(),
            "current_image_sha256": digest(entries[CURRENT.as_posix()]),
            "current_image_dimensions": [2048, 2048],
            "tracked_file_count": len(tracked),
            "contains_git_history_bundle": True,
            "excludes": [".git directory", ".venv", "API keys", "environment files", "caches"],
        }
        entries["BUNDLE_INFO.json"] = json.dumps(info, indent=2).encode("utf-8")
        checksums = "\n".join(f"{digest(data)}  {name}" for name, data in sorted(entries.items())) + "\n"
        entries["CONTENTS_SHA256.txt"] = checksums.encode("utf-8")

        with ZipFile(OUTPUT, "w", ZIP_DEFLATED, compresslevel=6) as archive:
            for name, data in sorted(entries.items()):
                archive.writestr(f"{PREFIX}/{name}", data)

    with ZipFile(OUTPUT) as archive:
        corrupt = archive.testzip()
        if corrupt:
            raise SystemExit(f"ZIP CRC failure: {corrupt}")
        names = set(archive.namelist())
        for relative in required:
            expected = f"{PREFIX}/{relative.as_posix()}"
            if expected not in names:
                raise SystemExit(f"Required ZIP entry missing: {expected}")
        if f"{PREFIX}/Gothic_Repair_Suite_History.bundle" not in names:
            raise SystemExit("Git history bundle missing")

    report = {
        "zip": str(OUTPUT),
        "sha256": digest(OUTPUT.read_bytes()),
        "bytes": OUTPUT.stat().st_size,
        "entries": len(names),
        "source_commit": info["source_commit"],
        "current_image_sha256": info["current_image_sha256"],
        "zip_integrity": True,
    }
    report_path = OUTPUT.with_suffix(".json")
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
