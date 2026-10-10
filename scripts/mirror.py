#!/usr/bin/env python3
"""Καθρέφτης των αγκυρών του AI Visibility Index.

Κατεβάζει το ευρετήριο `/methodology/seals/index.json` και, για κάθε άγκυρα που δεν υπάρχει ήδη εδώ,
τα αρχεία `list.txt` (τα ακριβή bytes που πήραν αποτύπωμα) και `<υπηρεσία>.tst` (η χρονοσφραγίδα RFC 3161).
Ό,τι έχει ήδη κατέβει δεν ξανακατεβαίνει και δεν ξαναγράφεται: οι άγκυρες είναι append-only και το ίδιο
ισχύει για αυτό το αποθετήριο. Μόνο η βιβλιοθήκη της Python, καμία εξάρτηση.

Mirrors the anchors of the AI Visibility Index (Greece). Standard library only, append-only.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = os.environ.get("AVI_BASE_URL", "https://ai-visibility-index-livid.vercel.app").rstrip("/")
ROOT = Path(__file__).resolve().parent.parent
ANCHORS = ROOT / "anchors"
UA = "avi-seals-mirror/1.0 (+https://github.com/christoskostouros/avi-seals)"


def fetch(path: str) -> bytes:
    req = urllib.request.Request(BASE + path, headers={"user-agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310 — fixed https base, paths from our own index
        return r.read()


def main() -> int:
    try:
        index = json.loads(fetch("/methodology/seals/index.json"))
    except urllib.error.HTTPError as e:
        # 404 = η σελίδα δεν έχει ακόμη το ευρετήριο (πριν το deploy)· 503 = η βάση δεν απάντησε. Όχι σφάλμα του καθρέφτη.
        print(f"index.json: HTTP {e.code} — nothing mirrored this run")
        return 0
    anchors = index.get("anchors", [])
    (ROOT / "index.json").write_bytes(json.dumps(index, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")
    new, checked = 0, 0
    for a in sorted(anchors, key=lambda x: x["id"]):
        d = ANCHORS / str(a["id"])
        meta = d / "meta.json"
        if meta.exists():
            checked += 1
            continue
        d.mkdir(parents=True, exist_ok=True)
        list_bytes = fetch(a["files"]["list"])
        digest = hashlib.sha256(list_bytes).hexdigest()
        if digest != a["list_sha256"]:
            print(f"anchor {a['id']}: list.txt sha256 {digest} != index {a['list_sha256']} — skipped, not written", file=sys.stderr)
            for p in d.iterdir():
                p.unlink()
            d.rmdir()
            continue
        (d / "list.txt").write_bytes(list_bytes)
        tokens = []
        for t in a["files"]["tokens"]:
            tst = fetch(t["file"])
            (d / f"{t['tsa']}.tst").write_bytes(tst)
            tokens.append({"tsa": t["tsa"], "gen_time": t.get("gen_time"), "file": f"{t['tsa']}.tst", "sha256": hashlib.sha256(tst).hexdigest()})
        meta.write_bytes(
            json.dumps(
                {"id": a["id"], "created_at": a["created_at"], "cohort_count": a["cohort_count"], "list_sha256": a["list_sha256"], "tokens": tokens, "source": BASE},
                ensure_ascii=False,
                indent=2,
            ).encode("utf-8")
            + b"\n"
        )
        new += 1
        print(f"anchor {a['id']}: mirrored ({a['cohort_count']} seals, {len(tokens)} timestamps)")
    print(f"done: {new} new, {checked} already present, {len(anchors)} in index")
    return 0


if __name__ == "__main__":
    sys.exit(main())
