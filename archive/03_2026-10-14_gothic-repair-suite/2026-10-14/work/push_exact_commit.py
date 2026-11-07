"""Upload the current Git commit through GitHub's Git Data API, preserving its SHA."""
from __future__ import annotations

import base64
import json
import subprocess
from pathlib import Path

import requests


ROOT = Path(__file__).parents[1]
REPO = "NeonButrfly/gothic-image-repair-suite"
API = f"https://api.github.com/repos/{REPO}/git"


def git(*args: str, binary: bool = False):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=not binary)


def main():
    token = subprocess.check_output(["gh", "auth", "token"], text=True).strip()
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                            "X-GitHub-Api-Version": "2022-11-28"})

    head = git("rev-parse", "HEAD").strip()
    tree_expected = git("rev-parse", "HEAD^{tree}").strip()
    parent = git("rev-parse", "HEAD^").strip()
    raw = git("ls-tree", "-r", "-z", "HEAD", binary=True)
    entries = []
    uploaded = 0
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", 1)
        mode, kind, local_sha = metadata.decode().split()
        path = raw_path.decode("utf-8")
        content = git("show", f"HEAD:{path}", binary=True)
        response = session.post(f"{API}/blobs", json={"content": base64.b64encode(content).decode(), "encoding": "base64"})
        response.raise_for_status()
        remote_sha = response.json()["sha"]
        if remote_sha != local_sha:
            raise RuntimeError(f"Blob SHA mismatch for {path}: {local_sha} != {remote_sha}")
        entries.append({"path": path, "mode": mode, "type": kind, "sha": remote_sha})
        uploaded += 1
        print(f"uploaded {uploaded}: {path}")

    response = session.post(f"{API}/trees", json={"tree": entries})
    response.raise_for_status()
    tree_actual = response.json()["sha"]
    if tree_actual != tree_expected:
        raise RuntimeError(f"Tree SHA mismatch: {tree_expected} != {tree_actual}")

    fields = git("show", "-s", "--format=%an%x00%ae%x00%aI%x00%cn%x00%ce%x00%cI%x00%B", "HEAD").split("\0", 6)
    author_name, author_email, author_date, committer_name, committer_email, committer_date, message = fields
    payload = {
        "message": message.rstrip("\n"), "tree": tree_actual, "parents": [parent],
        "author": {"name": author_name, "email": author_email, "date": author_date},
        "committer": {"name": committer_name, "email": committer_email, "date": committer_date},
    }
    response = session.post(f"{API}/commits", json=payload)
    response.raise_for_status()
    commit_actual = response.json()["sha"]
    if commit_actual != head:
        raise RuntimeError(f"Commit SHA mismatch: {head} != {commit_actual}")

    response = session.patch(f"{API}/refs/heads/main", json={"sha": head, "force": False})
    response.raise_for_status()
    print(json.dumps({"local_head": head, "remote_main": response.json()["object"]["sha"], "match": True}))


if __name__ == "__main__":
    main()
