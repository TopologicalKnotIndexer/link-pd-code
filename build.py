#!/usr/bin/env python3
"""Build the standalone link-pd-code C++17 executable."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shlex
import shutil
import subprocess
from typing import Sequence


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "src" / "main.cpp"


def command_parts(value: str) -> list[str]:
    path = Path(value)
    if path.is_file():
        return [str(path)]
    return shlex.split(value, posix=os.name != "nt")


def find_compiler(explicit: str | None) -> list[str]:
    configured = explicit or os.environ.get("CXX")
    candidates = [configured] if configured else ["g++", "clang++", "c++"]
    for candidate in candidates:
        if not candidate:
            continue
        parts = command_parts(candidate)
        executable = parts[0]
        if Path(executable).is_file() or shutil.which(executable):
            probe = subprocess.run(
                [*parts, "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            if probe.returncode == 0:
                return parts
    raise SystemExit("No g++-style C++17 compiler found; pass --cxx or set CXX.")


def copy_windows_runtime(compiler: list[str], output_dir: Path) -> None:
    if os.name != "nt":
        return
    executable = Path(shutil.which(compiler[0]) or compiler[0]).resolve()
    for name in (
        "libstdc++-6.dll",
        "libwinpthread-1.dll",
        "libgcc_s_seh-1.dll",
        "libgcc_s_dw2-1.dll",
        "libgcc_s_sjlj-1.dll",
    ):
        source = executable.parent / name
        if source.is_file():
            shutil.copy2(source, output_dir / name)


def build(argv: Sequence[str] | None = None) -> Path:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cxx", help="g++-style compiler command")
    parser.add_argument("--build-dir", default=str(ROOT / "build"))
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--portable", action="store_true", help="omit -march=native")
    parser.add_argument("--show-command", action="store_true")
    args = parser.parse_args(argv)

    compiler = find_compiler(args.cxx)
    output_dir = Path(args.build_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / ("link-pd-code.exe" if os.name == "nt" else "link-pd-code")
    flags = ["-std=c++17", "-Wall", "-Wextra", "-Wpedantic"]
    flags += ["-O0", "-g"] if args.debug else ["-O3", "-DNDEBUG"]
    if not args.portable:
        flags.append("-march=native")
    command = [*compiler, *flags, str(SOURCE), "-o", str(output)]
    if args.show_command:
        print("+ " + " ".join(command), flush=True)
    result = subprocess.run(command, cwd=ROOT, check=False)
    if result.returncode != 0 and os.name != "nt":
        result = subprocess.run([*command, "-lstdc++fs"], cwd=ROOT, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    copy_windows_runtime(compiler, output_dir)
    print(f"Built {output}")
    return output


if __name__ == "__main__":
    build()
