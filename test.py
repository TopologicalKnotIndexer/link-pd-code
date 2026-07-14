#!/usr/bin/env python3
"""Build and test the link-pd-code command-line projection engine."""

from __future__ import annotations

import argparse
import ast
from collections import Counter
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent
EXE_NAME = "link-pd-code.exe" if os.name == "nt" else "link-pd-code"


def run(executable: Path, args: list[str], *, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(executable), *args],
        cwd=ROOT,
        input=stdin,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=60,
    )


def assert_valid_pd(text: str) -> None:
    value = ast.literal_eval(text.strip())
    if not isinstance(value, list):
        raise AssertionError(value)
    counts = Counter()
    for crossing in value:
        if not isinstance(crossing, list) or len(crossing) != 4:
            raise AssertionError(crossing)
        counts.update(crossing)
    expected = set(range(1, 2 * len(value) + 1))
    if set(counts) != expected or any(count != 2 for count in counts.values()):
        raise AssertionError(value)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cxx")
    parser.add_argument("--build-dir", default=str(ROOT / "build"))
    parser.add_argument("--portable", action="store_true")
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()

    build_dir = Path(args.build_dir).resolve()
    executable = build_dir / EXE_NAME
    if args.rebuild or not executable.is_file():
        command = [sys.executable, str(ROOT / "build.py"), "--build-dir", str(build_dir)]
        if args.cxx:
            command += ["--cxx", args.cxx]
        if args.portable:
            command.append("--portable")
        subprocess.run(command, cwd=ROOT, check=True)

    square = """1
4
0 0 0
1 0 0
1 1 0
0 1 0
"""
    result = run(executable, ["--direction", "0", "0", "1"], stdin=square)
    assert result.returncode == 0 and result.stdout.strip() == "[]", result
    encoded = run(
        executable,
        ["--direction", "0", "0", "1", "--encode-isolated-components"],
        stdin=square,
    )
    assert encoded.returncode == 0 and encoded.stdout.strip() == "[[1,1,2,2]]", encoded

    crossing = """1
4
-1 -1 0
1 1 0
1 -1 1
-1 1 1
"""
    result = run(executable, ["--direction", "0", "0", "1", "--first-generic"], stdin=crossing)
    assert result.returncode == 0, result.stderr
    assert_valid_pd(result.stdout)

    endpoint_touch = """1
4
0 0 0
1 0 0
1 -1 1
1 1 1
"""
    rejected = run(executable, ["--direction", "0", "0", "1"], stdin=endpoint_touch)
    assert rejected.returncode != 0 and "non-generic" in rejected.stderr, rejected

    samples = sorted((ROOT / "test_data" / "Knot").glob("*/data.txt"))
    if len(samples) != 22:
        raise AssertionError(f"expected 22 committed knot samples, found {len(samples)}")
    for sample in samples:
        result = run(executable, ["--first-generic", "--max-attempts", "64", "--input", str(sample)])
        if result.returncode != 0:
            raise AssertionError(f"{sample}: {result.stderr}")
        assert_valid_pd(result.stdout)

    with tempfile.TemporaryDirectory(prefix="link_pd_code_unicode_") as tmp:
        folder = Path(tmp) / "中文路径"
        folder.mkdir()
        source = folder / "坐标.txt"
        target = folder / "结果.txt"
        source.write_text(square, encoding="utf-8")
        result = run(
            executable,
            ["--direction", "0", "0", "1", "--input", str(source), "--output", str(target)],
        )
        assert result.returncode == 0 and target.read_text(encoding="utf-8").strip() == "[]", result

    print("link-pd-code tests passed: CLI, degeneracies, Unicode paths, 22 coordinate samples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
