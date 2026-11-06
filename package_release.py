"""Create a user-installable Release ZIP from verified patch data."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import tempfile
import zipfile

PROJECT = Path(__file__).resolve().parent.parent


def package_release(patch_data, output_directory):
    version = (PROJECT / "VERSION").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[a-zA-Z0-9.]+)?", version):
        raise ValueError("Invalid VERSION")
    data = patch_data.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    with zipfile.ZipFile(patch_data) as archive:
        if archive.testzip() is not None:
            raise ValueError("PatchData.zip failed CRC verification")
        manifest = json.loads(archive.read("manifest.json"))
        if manifest.get("format") != 1:
            raise ValueError("Unsupported patch data format")
        for entry in manifest["files"]:
            if not re.fullmatch(r"level\d+|sharedassets\d+\.assets", entry["path"]):
                raise ValueError("Unexpected resource path")
            archive.getinfo(entry["literal_entry"])
    compatibility = json.loads(
        (PROJECT / "metadata/compatibility.json").read_text(encoding="utf-8")
    )
    expected = {entry["path"]: entry["sha256"] for entry in compatibility["original_files"]}
    actual = {entry["path"]: entry["original_sha256"] for entry in manifest["files"]}
    if actual != expected or manifest["build"] != compatibility["build"]:
        raise ValueError("Patch data does not match this repository compatibility manifest")
    output_directory.mkdir(parents=True, exist_ok=True)
    destination = output_directory / f"NITW-Xbox-CN-v{version}-win-x64.zip"
    with tempfile.TemporaryDirectory(prefix="nitw-release-") as temporary:
        root = Path(temporary) / "NITW-Xbox-CN"
        root.mkdir()
        for path in (PROJECT / "installer").iterdir():
            if path.suffix not in (".ps1", ".cmd"):
                continue
            content = path.read_bytes()
            if path.name == "Install.ps1":
                text = content.decode("utf-8-sig")
                if "__ARCHIVE_SHA__" not in text:
                    raise ValueError("Installer template must contain its checksum placeholder")
                content = text.replace("__ARCHIVE_SHA__", digest).encode("utf-8-sig")
            elif path.suffix == ".cmd":
                content = content.replace(b"v0.1.0-beta.1", ("v" + version).encode("ascii"))
            (root / path.name).write_bytes(content)
        (root / "PatchData.zip").write_bytes(data)
        (root / "README.md").write_bytes((PROJECT / "docs/INSTALL.md").read_bytes())
        (root / "CREDITS.md").write_bytes((PROJECT / "CREDITS.md").read_bytes())
        (root / "LICENSE").write_bytes((PROJECT / "LICENSE").read_bytes())
        (root / "licenses").mkdir()
        for path in (PROJECT / "licenses").iterdir():
            if path.is_file():
                (root / "licenses" / path.name).write_bytes(path.read_bytes())
        metadata = root / "metadata"
        metadata.mkdir()
        for path in (PROJECT / "metadata").glob("*.json"):
            (metadata / path.name).write_bytes(path.read_bytes())
        build_info = {key: value for key, value in manifest.items() if key != "files"}
        (metadata / "BuildInfo.json").write_text(
            json.dumps(build_info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        files = sorted(path for path in root.rglob("*") if path.is_file())
        sums = [
            hashlib.sha256(path.read_bytes()).hexdigest() + "  " + path.relative_to(root).as_posix()
            for path in files
        ]
        (root / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n", encoding="ascii")
        with zipfile.ZipFile(
            destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6
        ) as archive:
            for path in sorted(root.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(root.parent).as_posix())
        with zipfile.ZipFile(destination) as archive:
            if archive.testzip() is not None:
                raise ValueError("Release archive failed CRC verification")
    checksum = hashlib.sha256(destination.read_bytes()).hexdigest()
    destination.with_suffix(".zip.sha256").write_text(
        checksum + "  " + destination.name + "\n", encoding="ascii"
    )
    print("Release package:", destination.name)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--patch-data", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path, default=PROJECT / "dist/release-assets")
    args = parser.parse_args()
    package_release(args.patch_data, args.output_dir)


if __name__ == "__main__":
    main()
