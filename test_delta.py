import hashlib
import importlib.util
import json
from pathlib import Path
import random
import tempfile
import unittest

PROJECT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("patch_packer", PROJECT / "src/pack_patch.py")
PACKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKER)


class DeltaTests(unittest.TestCase):
    def test_empty_identical_and_repeated_data(self):
        for old, new in [
            (b"", b""),
            (b"", b"new"),
            (b"old", b""),
            (b"x" * 20000, b"x" * 20000),
            (bytes(40000), b"prefix" + bytes(40000)),
        ]:
            with self.subTest(original_size=len(old), new_size=len(new)):
                operations, literals = PACKER.delta(old, new)
                self.assertEqual(PACKER.apply(old, operations, literals), new)

    def test_random_mutations_and_unaligned_insertions(self):
        rng = random.Random(20261106)
        for _ in range(25):
            old = rng.randbytes(12000)
            start = rng.randrange(1, 8000)
            new = (
                old[:start]
                + rng.randbytes(rng.randrange(1, 25))
                + old[start + rng.randrange(0, 300) :]
            )
            operations, literals = PACKER.delta(old, new)
            self.assertEqual(PACKER.apply(old, operations, literals), new)

    def test_invalid_operations_are_rejected(self):
        for operation in [("x", 0, 1), ("c", -1, 1), ("a", 0, -1), ("c", 0, 99)]:
            with self.subTest(operation=operation):
                with self.assertRaises(ValueError):
                    PACKER.apply(b"abc", [operation], b"def")

    def test_wrong_baseline_does_not_overwrite_existing_package(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            game, build, out = root / "game", root / "build", root / "out"
            for path in [game, build / "input", out]:
                path.mkdir(parents=True)
            (game / "level0").write_bytes(b"wrong baseline")
            (build / "input/level0").write_bytes(b"target")
            entry = {
                "path": "level0",
                "mode": "input",
                "original_sha256": hashlib.sha256(b"expected baseline").hexdigest(),
                "target_sha256": hashlib.sha256(b"target").hexdigest(),
            }
            (build / "manifest-files.json").write_text(json.dumps([entry]), encoding="utf-8")
            (out / "PatchData.zip").write_bytes(b"previous release")
            with self.assertRaises(ValueError):
                PACKER.pack(game, build, out)
            self.assertEqual((out / "PatchData.zip").read_bytes(), b"previous release")


if __name__ == "__main__":
    unittest.main()
