"""Fetch the pinned Compara / Ensembl inputs and record what was fetched.

Downloads go to ``data/compara/`` (gitignored -- large), and every file's source URL, the
provider's published checksum, our locally computed SHA-256 and the fetch date are appended to
``data/PROVENANCE.md``, so the repo stays reproducible-by-reference without committing bytes.

Run:  python -m logs_orthology.fetch
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import sys
from pathlib import Path

import requests

from . import sources
from .sources import SourceFile

CHUNK = 1 << 20  # 1 MiB
#: A download sending no bytes for this long is dead, whatever the overall timeout says.
BODY_STALL_TIMEOUT = 120


# ---------------------------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------------------------

def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def data_dir() -> Path:
    d = project_root() / "data" / "compara"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = sources.USER_AGENT
    return s


# ---------------------------------------------------------------------------------------------
# Checksums
# ---------------------------------------------------------------------------------------------

def bsd_sum(path: Path) -> str:
    """The classic UNIX ``sum`` (BSD algorithm): 16-bit rotating checksum + 1 KiB block count.

    Ensembl publishes this, not MD5, in the ``CHECKSUMS`` files under ``gtf/`` and ``tsv/``. It
    is a weak check, but a weak verification that runs beats a strong one that does not: the
    alternative here is no check at all, and a truncated reference file is exactly the input
    whose corruption stays invisible until it has already skewed a result.
    """
    csum = 0
    size = 0
    with open(path, "rb") as fh:
        while chunk := fh.read(CHUNK):
            size += len(chunk)
            for byte in chunk:
                csum = (csum >> 1) + ((csum & 1) << 15)
                csum = (csum + byte) & 0xFFFF
    return f"{csum} {-(-size // 1024)}"  # checksum + ceil(size / 1024)


def md5_of(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as fh:
        while chunk := fh.read(CHUNK):
            h.update(chunk)
    return h.hexdigest()


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while chunk := fh.read(CHUNK):
            h.update(chunk)
    return h.hexdigest()


def published_checksum(sess: requests.Session, sf: SourceFile) -> tuple[str, str | None]:
    """Whatever checksum the provider publishes for this file: ``(kind, value)``.

    ``kind`` is ``"md5"``, ``"sum"`` or ``"none"``. Tries the strong manifest first, falls back
    to the weak one, and never invents a pass.
    """
    base = sf.url.rsplit("/", 1)[0]
    try:
        r = sess.get(f"{base}/MD5SUM", timeout=60)
        if r.status_code == 200:
            for line in r.text.splitlines():
                parts = line.split()
                if len(parts) == 2 and parts[1] == sf.md5_name:
                    return "md5", parts[0]
    except requests.RequestException:
        pass
    try:
        r = sess.get(f"{base}/CHECKSUMS", timeout=60)
        if r.status_code == 200:
            for line in r.text.splitlines():
                parts = line.split()
                if len(parts) == 3 and parts[2] == sf.md5_name:  # "<sum> <blocks> <name>"
                    return "sum", f"{int(parts[0])} {int(parts[1])}"
    except requests.RequestException:
        pass
    return "none", None


def observe(path: Path, kind: str) -> str:
    if kind == "md5":
        return md5_of(path)
    if kind == "sum":
        return bsd_sum(path)
    return "(none published)"


# ---------------------------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------------------------

def download(sess: requests.Session, sf: SourceFile, dest: Path, force: bool = False) -> dict:
    """Download one file, verify it, and return a provenance record.

    Writes to ``<name>.partial`` and moves into place only after verification, so an interrupted
    run never leaves a truncated file a later run would mistake for complete.
    """
    kind, expected = published_checksum(sess, sf)

    if dest.exists() and not force:
        got = observe(dest, kind)
        if kind == "none" or got == expected:
            print(f"  [cached] {dest.name}  ({dest.stat().st_size / 1e6:.1f} MB)")
            return _record(sf, dest, kind, expected, got, cached=True)
        print(f"  [stale]  {dest.name}: {kind} {got} != published {expected}; re-downloading")

    partial = dest.with_name(dest.name + ".partial")
    got_bytes = 0
    with sess.get(sf.url, timeout=(30, BODY_STALL_TIMEOUT), stream=True) as r:
        r.raise_for_status()
        total = int(r.headers.get("Content-Length", 0))
        with open(partial, "wb") as fh:
            for chunk in r.iter_content(CHUNK):
                fh.write(chunk)
                got_bytes += len(chunk)
                if total:
                    print(f"\r  {dest.name}: {got_bytes/1e6:7.1f} / {total/1e6:.1f} MB "
                          f"({100*got_bytes/total:5.1f}%)", end="", flush=True)
    print()

    got = observe(partial, kind)
    if kind != "none" and got != expected:
        partial.unlink(missing_ok=True)
        raise RuntimeError(
            f"{sf.key}: {kind} mismatch. published={expected} computed={got}. "
            "Refusing to keep the file -- a silently wrong input is worse than a missing one."
        )
    partial.replace(dest)
    return _record(sf, dest, kind, expected, got, cached=False)


def _record(sf: SourceFile, dest: Path, kind: str, expected: str | None, observed: str,
            cached: bool) -> dict:
    return {
        "key": sf.key,
        "url": sf.url,
        "local_path": str(dest.relative_to(project_root())).replace("\\", "/"),
        "bytes": dest.stat().st_size,
        "checksum_kind": kind,
        "checksum_published": expected or "(not published)",
        "checksum_observed": observed,
        "verified": kind != "none" and observed == expected,
        "sha256": sha256_of(dest),
        "source": sources.SOURCE,
        "release": sources.RELEASE,
        "fetched": _dt.date.today().isoformat(),
        "cached": cached,
        "description": sf.description,
    }


# ---------------------------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------------------------

def write_provenance(records: list[dict]) -> Path:
    path = project_root() / "data" / "PROVENANCE.md"
    today = _dt.date.today().isoformat()
    lines = [
        "",
        f"## Ensembl release {sources.RELEASE} — fetched {today}",
        "",
        "Pinned inputs for the cross-species orthology snapshot. The bytes are gitignored; this",
        "table is their record. A release bump is a **new snapshot**, never an in-place update.",
        "",
        "| File | Local path | Bytes | Checksum | Verified | SHA-256 |",
        "|---|---|---|---|---|---|",
    ]
    for r in records:
        if r["checksum_kind"] == "none":
            verified = "— *(none published)*"
        else:
            verified = "✅" if r["verified"] else "❌"
        lines.append(
            f"| [`{r['key']}`]({r['url']}) | `{r['local_path']}` | {r['bytes']:,} | "
            f"`{r['checksum_kind']}:{r['checksum_published']}` | {verified} | "
            f"`{r['sha256'][:16]}…` |"
        )
    lines += [
        "",
        "**Redundancy caveat, from the provider's own README:** each genome-specific homology",
        "file holds *an arbitrary subset* of the orthologies involving that genome. The human",
        "file alone does **not** contain every human↔mouse orthology. All three taxa are fetched",
        "and unioned; taking one would undercount silently.",
        "",
        "**Checksum note:** Ensembl publishes MD5 under `tsv/ensembl-compara/`, but only the",
        "classic BSD `sum` (16-bit checksum + 1 KiB block count) under `gtf/` and `tsv/`. Both",
        "are checked; the kind actually used is recorded per row above. The gene-tree content",
        "dump has no published checksum at all, which is recorded rather than glossed.",
        "",
    ]
    with open(path, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Fetch pinned Ensembl / Compara inputs.")
    ap.add_argument("--force", action="store_true", help="re-download even if cached and valid")
    ap.add_argument("--only", help="substring filter on the source key (e.g. 'xref')")
    args = ap.parse_args(argv)

    sess = _session()
    dest_dir = data_dir()
    files = [f for f in sources.all_files() if not args.only or args.only in f.key]

    print(f"Ensembl release {sources.RELEASE} — {len(files)} file(s) -> {dest_dir}")
    records = []
    for sf in files:
        print(f"- {sf.key}")
        records.append(download(sess, sf, dest_dir / sf.local_name, force=args.force))

    print(f"\nProvenance appended to {write_provenance(records)}")
    unverified = [r["key"] for r in records if r["checksum_kind"] == "none"]
    if unverified:
        print(f"NOTE: no checksum published for: {', '.join(unverified)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
