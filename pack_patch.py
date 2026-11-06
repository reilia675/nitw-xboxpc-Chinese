"""Pack copy/literal resource deltas; never ship the installed game files."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

PROJECT = Path(__file__).resolve().parent.parent


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def delta(old, new):
    """Return copy/add operations and their literal bytes."""
    block = 64
    index = {old[p : p + block]: p for p in range(0, max(0, len(old) - block + 1), 128)}
    operations = []
    literals = bytearray()
    position = 0
    literal_start = 0

    def add_literal(start, end):
        if end > start:
            operations.append(["a", len(literals), end - start])
            literals.extend(new[start:end])

    while position + block <= len(new):
        source = index.get(new[position : position + block])
        if source is None:
            position += 8
            continue
        length = block
        for step in (4096, 128, 8, 1):
            while (
                position + length + step <= len(new)
                and source + length + step <= len(old)
                and new[position + length : position + length + step]
                == old[source + length : source + length + step]
            ):
                length += step
        if length < 128:
            position += 8
            continue
        add_literal(literal_start, position)
        if (
            operations
            and operations[-1][0] == "c"
            and operations[-1][1] + operations[-1][2] == source
        ):
            operations[-1][2] += length
        else:
            operations.append(["c", source, length])
        position += length
        literal_start = position
    add_literal(literal_start, len(new))
    return operations, bytes(literals)


def apply(old, operations, literals):
    """Reference decoder used to verify every delta before packaging."""
    output = []
    for kind, offset, length in operations:
        if kind not in ("c", "a") or offset < 0 or length < 0:
            raise ValueError("Invalid patch operation")
        source = old if kind == "c" else literals
        if offset + length > len(source):
            raise ValueError("Patch operation exceeds source bounds")
        output.append(source[offset : offset + length])
    return b"".join(output)


def pack(game_data, build_directory, output_directory):
    files = json.loads((build_directory / "manifest-files.json").read_text(encoding="utf-8"))
    # Check the complete baseline before opening the output archive.
    for entry in files:
        if not re.fullmatch(r"level\d+|sharedassets\d+\.assets", entry["path"]):
            raise ValueError("Unexpected resource name")
        if entry["mode"] not in ("input", "chinese"):
            raise ValueError("Unexpected patch mode")
        original = (game_data / entry["path"]).read_bytes()
        target = (build_directory / entry["mode"] / entry["path"]).read_bytes()
        if sha256(original) != entry["original_sha256"] or sha256(target) != entry["target_sha256"]:
            raise ValueError("Build/source checksum mismatch: " + entry["path"])
    manifest = {
        "format": 1,
        "game": "Night in the Woods Xbox Win10",
        "build": "Unity 5.6.2p4 / Xbox 1.0.0.0",
        "status": "experimental-offline-validated",
        "files": files,
        "statistics": json.loads((build_directory / "stats.json").read_text(encoding="utf-8")),
    }
    output_directory.mkdir(parents=True, exist_ok=True)
    archive_path = output_directory / "PatchData.zip"
    pending = output_directory / "PatchData.zip.building"
    with zipfile.ZipFile(
        pending, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for index, entry in enumerate(files):
            old = (game_data / entry["path"]).read_bytes()
            new = (build_directory / entry["mode"] / entry["path"]).read_bytes()
            operations, literals = delta(old, new)
            if apply(old, operations, literals) != new:
                raise ValueError("Delta reconstruction failed: " + entry["path"])
            entry.update(ops=operations, literal_entry=f"literals/{index}.bin")
            archive.writestr(entry["literal_entry"], literals)
        archive.writestr(
            "manifest.json", json.dumps(manifest, ensure_ascii=False, separators=(",", ":"))
        )
    pending.replace(archive_path)
    summary = {key: value for key, value in manifest.items() if key != "files"}
    (output_directory / "BuildInfo.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Packed and verified {len(files)} resource deltas.")
    return archive_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-data", required=True, type=Path)
    parser.add_argument("--build-dir", type=Path, default=PROJECT / "build")
    parser.add_argument("--output-dir", type=Path, default=PROJECT / "dist/NITW-Xbox-CN")
    args = parser.parse_args()
    pack(args.game_data, args.build_dir, args.output_dir)


if __name__ == "__main__":
    main()
