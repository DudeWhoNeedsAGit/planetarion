#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import pathlib
import shlex
import subprocess
import sys
from typing import Iterable, Sequence


def _path(p: str) -> pathlib.Path:
    return pathlib.Path(p).expanduser()


def _which_python(project_root: pathlib.Path, python: str | None) -> str:
    if python:
        candidate = pathlib.Path(python).expanduser()
        if candidate.exists():
            # Do NOT resolve symlinks here: venv/bin/python is commonly a symlink to the
            # system interpreter, but its *path* is what activates the venv site-packages.
            return str(candidate.absolute() if candidate.is_absolute() else (pathlib.Path.cwd() / candidate).absolute())
        if not candidate.is_absolute():
            from_cwd = (pathlib.Path.cwd() / candidate).absolute()
            if from_cwd.exists():
                return str(from_cwd)
        # Fall back to trusting the value as an executable name on PATH.
        return python

    candidates = [
        project_root / "venv" / "bin" / "python",
        project_root / ".venv" / "bin" / "python",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return "python3"


def _module_available(python: str, module: str) -> bool:
    try:
        res = subprocess.run(
            [python, "-c", f"import {module}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return res.returncode == 0
    except FileNotFoundError:
        return False


def _run(
    *,
    title: str,
    cmd: Sequence[str],
    cwd: pathlib.Path,
    env: dict[str, str],
) -> None:
    print(f"\n== {title} ==")
    print("$ " + " ".join(shlex.quote(x) for x in cmd))
    res = subprocess.run(cmd, cwd=str(cwd), env=env, check=False)
    if res.returncode != 0:
        raise SystemExit(res.returncode)


def _parse_cmd(cmd: str) -> list[str]:
    return shlex.split(cmd)


def _inject_coverage(
    *,
    python: str,
    cmd: Sequence[str],
    rcfile: pathlib.Path,
    parallel_mode: bool,
) -> list[str] | None:
    if not cmd:
        return None

    exe = os.path.basename(cmd[0])
    is_python = exe.startswith("python") or cmd[0] == python
    is_pytest = exe in {"pytest", "py.test"}

    parallel_args = ["--parallel-mode"] if parallel_mode else []

    if is_python:
        # If the user wrote `python ...`, prefer the selected interpreter (often a venv path).
        python0 = cmd[0]
        python0_base = os.path.basename(python0)
        if python0 in {"python", "python3", "py"} or python0_base.startswith("python"):
            python0 = python
        # If the caller is already explicitly using coverage, don't double-wrap.
        if len(cmd) >= 3 and cmd[1:3] == ["-m", "coverage"]:
            return list(cmd)
        return [
            python0,
            "-m",
            "coverage",
            "run",
            "--rcfile",
            str(rcfile),
            *parallel_args,
            *cmd[1:],
        ]

    if is_pytest:
        return [
            python,
            "-m",
            "coverage",
            "run",
            "--rcfile",
            str(rcfile),
            *parallel_args,
            "-m",
            "pytest",
            *cmd[1:],
        ]

    return None


def _write_coveragerc(
    *,
    out_dir: pathlib.Path,
    project_root: pathlib.Path,
    sources: Sequence[pathlib.Path],
) -> pathlib.Path:
    rcfile = out_dir / ".coveragerc"
    source_lines = "\n".join(f"    {p}" for p in sources)
    rcfile.write_text(
        "\n".join(
            [
                "[run]",
                "branch = True",
                "parallel = True",
                "source =",
                source_lines or f"    {project_root}",
                "omit =",
                "    */tests/*",
                "    */test/*",
                "    */venv/*",
                "    */.venv/*",
                "    */site-packages/*",
                "    */__pycache__/*",
                "",
                "[report]",
                "skip_covered = True",
                "show_missing = True",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return rcfile


def _load_coverage_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_file_key(project_root: pathlib.Path, key: str) -> str:
    p = pathlib.Path(key)
    if not p.is_absolute():
        p = project_root / p
    try:
        return str(p.resolve())
    except FileNotFoundError:
        return str(p)


def _parse_vulture_output(project_root: pathlib.Path, text: str) -> list[dict]:
    findings: list[dict] = []
    for line in text.splitlines():
        # Typical line: path/to/file.py:123: Unused function 'foo'
        parts = line.split(":", 2)
        if len(parts) != 3:
            continue
        file_part, line_part, msg = parts
        try:
            line_no = int(line_part.strip())
        except ValueError:
            continue
        file_path = pathlib.Path(file_part.strip())
        if not file_path.is_absolute():
            file_path = project_root / file_path
        findings.append(
            {
                "file": str(file_path.resolve()),
                "line": line_no,
                "message": msg.strip(),
            }
        )
    return findings


def _iter_source_files(sources: Sequence[pathlib.Path]) -> Iterable[pathlib.Path]:
    for source in sources:
        if source.is_file() and source.suffix == ".py":
            yield source
            continue
        if source.is_dir():
            yield from source.rglob("*.py")


def _write_report(
    *,
    out_dir: pathlib.Path,
    project_root: pathlib.Path,
    sources: Sequence[pathlib.Path],
    coverage_json_path: pathlib.Path | None,
    vulture_txt_path: pathlib.Path | None,
) -> pathlib.Path:
    lines: list[str] = []
    lines.append("# Dead code tracer report")
    lines.append("")
    lines.append(f"- Project root: `{project_root}`")
    lines.append(f"- Generated: `{_dt.datetime.now().isoformat(timespec='seconds')}`")
    lines.append("")

    coverage_data = None
    if coverage_json_path and coverage_json_path.exists():
        coverage_data = _load_coverage_json(coverage_json_path)

    vulture_findings: list[dict] = []
    if vulture_txt_path and vulture_txt_path.exists():
        vulture_findings = _parse_vulture_output(
            project_root=project_root,
            text=vulture_txt_path.read_text(encoding="utf-8", errors="replace"),
        )

    if coverage_data:
        files = coverage_data.get("files", {}) or {}
        normalized = {
            _normalize_file_key(project_root, k): v for k, v in files.items()
        }

        never_executed: list[tuple[str, float, int]] = []
        for file_path, payload in normalized.items():
            summary = (payload or {}).get("summary", {}) or {}
            num_statements = int(summary.get("num_statements") or 0)
            covered_lines = int(summary.get("covered_lines") or 0)
            percent = float(summary.get("percent_covered") or 0.0)
            if num_statements <= 0:
                continue
            if covered_lines == 0:
                never_executed.append((file_path, percent, num_statements))

        never_executed.sort(key=lambda t: (-t[2], t[0]))

        lines.append("## Coverage highlights")
        lines.append("")
        lines.append(f"- Coverage JSON: `{coverage_json_path}`")
        if never_executed:
            lines.append("- Files with **0 executed lines** (likely dead/unreached paths):")
            for file_path, _pct, num in never_executed[:50]:
                rel = os.path.relpath(file_path, start=str(project_root))
                lines.append(f"  - `{rel}` ({num} statements)")
        else:
            lines.append("- No files with 0 executed lines found in measured sources.")
        lines.append("")

        if vulture_findings:
            executed_by_file: dict[str, set[int]] = {}
            missing_by_file: dict[str, set[int]] = {}
            for file_path, payload in normalized.items():
                executed_by_file[file_path] = set(payload.get("executed_lines") or [])
                missing_by_file[file_path] = set(payload.get("missing_lines") or [])

            dead_like: list[dict] = []
            maybe_dynamic: list[dict] = []
            for f in vulture_findings:
                file_path = f["file"]
                line_no = int(f["line"])
                executed = line_no in executed_by_file.get(file_path, set())
                missing = line_no in missing_by_file.get(file_path, set())
                if missing and not executed:
                    dead_like.append(f)
                else:
                    maybe_dynamic.append(f)

            lines.append("## Vulture vs coverage")
            lines.append("")
            lines.append(
                "- High-confidence: vulture flags that are also **not executed** in this run."
            )
            if dead_like:
                for f in dead_like[:200]:
                    rel = os.path.relpath(f["file"], start=str(project_root))
                    lines.append(f"  - `{rel}:{f['line']}` {f['message']}")
            else:
                lines.append("  - (none)")
            lines.append("")
            lines.append(
                "- Lower-confidence: vulture flags that **might be executed** (dynamic calls, reflection, tests, etc.)."
            )
            if maybe_dynamic:
                for f in maybe_dynamic[:50]:
                    rel = os.path.relpath(f["file"], start=str(project_root))
                    lines.append(f"  - `{rel}:{f['line']}` {f['message']}")
            else:
                lines.append("  - (none)")
            lines.append("")

    if vulture_findings and not coverage_data:
        lines.append("## Vulture findings")
        lines.append("")
        lines.append(f"- Vulture output: `{vulture_txt_path}`")
        for f in vulture_findings[:200]:
            rel = os.path.relpath(f["file"], start=str(project_root))
            lines.append(f"  - `{rel}:{f['line']}` {f['message']}")
        lines.append("")

    if not coverage_data and not vulture_findings:
        lines.append("## No data")
        lines.append("")
        lines.append(
            "- Neither coverage nor vulture results were produced. See the console output for install/help text."
        )
        lines.append("")

    lines.append("## Next steps")
    lines.append("")
    lines.append("- Delete code only after confirming it stays unreferenced in:")
    lines.append("  - unit/integration tests")
    lines.append("  - E2E flows (Playwright)")
    lines.append("  - a short manual play session")
    lines.append("")
    lines.append("- Prefer refactors:")
    lines.append("  - remove unused imports first")
    lines.append("  - remove unused helper functions next")
    lines.append("  - remove entire modules last")
    lines.append("")

    report = out_dir / "deadcode_report.md"
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Combine dynamic coverage + vulture static analysis to surface likely dead code."
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Root of the Python project to analyze (default: .)",
    )
    parser.add_argument(
        "--python",
        default=None,
        help="Python interpreter to use (default: auto-detect venv/.venv/game-server/venv, else python3)",
    )
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        help="Source path(s) to measure/analyze (repeatable). Default: <project-root>/src if it exists, else <project-root>.",
    )
    parser.add_argument(
        "--tests",
        default="python -m pytest",
        help='Test command to run (default: "python -m pytest"). If not a python/pytest command (e.g. make), coverage injection is skipped.',
    )
    parser.add_argument(
        "--run",
        default=None,
        help="Optional command to run under coverage after tests (e.g. start server and do a short manual session, then Ctrl-C).",
    )
    parser.add_argument(
        "--min-confidence",
        type=int,
        default=70,
        help="Vulture min confidence (default: 70).",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output directory for artifacts (default: <project-root>/.deadcode/<timestamp>).",
    )
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Skip dynamic coverage collection.",
    )
    parser.add_argument(
        "--no-vulture",
        action="store_true",
        help="Skip vulture static analysis.",
    )
    parser.add_argument(
        "--vulture-exclude",
        action="append",
        default=["venv", ".venv", "__pycache__", ".pytest_cache", "site-packages"],
        help="Exclude paths for vulture (repeatable). Default excludes common venv/cache dirs.",
    )
    parser.add_argument(
        "--env",
        action="append",
        default=[],
        help="Extra env var(s) like KEY=VALUE (repeatable).",
    )
    args = parser.parse_args(list(argv))

    project_root = _path(args.project_root).resolve()
    python = _which_python(project_root, args.python)

    sources = [_path(p) for p in args.source]
    if not sources:
        default_src = project_root / "src"
        sources = [default_src if default_src.exists() else project_root]
    sources = [(project_root / p if not p.is_absolute() else p).resolve() for p in sources]

    timestamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = _path(args.out).resolve() if args.out else (project_root / ".deadcode" / timestamp)
    out_dir.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    env["PYTHONUNBUFFERED"] = "1"
    for item in args.env:
        if "=" not in item:
            raise SystemExit(f"--env expects KEY=VALUE, got: {item!r}")
        k, v = item.split("=", 1)
        env[k] = v

    # If this project has a src/ folder, it's commonly intended to be on PYTHONPATH.
    src_dir = project_root / "src"
    if src_dir.exists():
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = str(src_dir) + (os.pathsep + existing if existing else "")

    coverage_json_path: pathlib.Path | None = None
    vulture_txt_path: pathlib.Path | None = None

    rcfile = _write_coveragerc(out_dir=out_dir, project_root=project_root, sources=sources)

    # Allow reusing prior artifacts if the user points --out at an existing run directory.
    if args.no_coverage:
        existing_coverage = out_dir / "coverage.json"
        if existing_coverage.exists():
            coverage_json_path = existing_coverage
    if args.no_vulture:
        existing_vulture = out_dir / "vulture.txt"
        if existing_vulture.exists():
            vulture_txt_path = existing_vulture

    if not args.no_coverage:
        if not _module_available(python, "coverage"):
            print(
                f"coverage is not installed for {python!r}. Install it in your venv, e.g.\n"
                f"  {shlex.quote(python)} -m pip install coverage\n"
            )
        else:
            env_cov = dict(env)
            env_cov["COVERAGE_FILE"] = str(out_dir / ".coverage")

            _run(
                title="coverage: erase",
                cmd=[python, "-m", "coverage", "erase", "--rcfile", str(rcfile)],
                cwd=project_root,
                env=env_cov,
            )

            tests_cmd = _parse_cmd(args.tests)
            injected = _inject_coverage(
                python=python, cmd=tests_cmd, rcfile=rcfile, parallel_mode=True
            )
            if injected is None:
                print(
                    "Tests command is not a python/pytest invocation, so coverage injection is skipped.\n"
                    f"Tests command: {args.tests!r}\n"
                    "Tip: pass a python command (e.g. 'python -m pytest ...') to enable coverage.\n"
                )
                _run(title="tests (no coverage)", cmd=tests_cmd, cwd=project_root, env=env)
            else:
                _run(title="tests (coverage)", cmd=injected, cwd=project_root, env=env_cov)

            if args.run:
                run_cmd = _parse_cmd(args.run)
                injected_run = _inject_coverage(
                    python=python, cmd=run_cmd, rcfile=rcfile, parallel_mode=True
                )
                if injected_run is None:
                    print(
                        "Run command is not a python/pytest invocation, so coverage injection is skipped.\n"
                        f"Run command: {args.run!r}\n"
                    )
                    _run(title="run (no coverage)", cmd=run_cmd, cwd=project_root, env=env)
                else:
                    _run(title="run (coverage)", cmd=injected_run, cwd=project_root, env=env_cov)

            _run(
                title="coverage: combine",
                cmd=[python, "-m", "coverage", "combine", "--rcfile", str(rcfile)],
                cwd=project_root,
                env=env_cov,
            )
            coverage_json_path = out_dir / "coverage.json"
            _run(
                title="coverage: json",
                cmd=[
                    python,
                    "-m",
                    "coverage",
                    "json",
                    "--rcfile",
                    str(rcfile),
                    "-o",
                    str(coverage_json_path),
                ],
                cwd=project_root,
                env=env_cov,
            )

    if not args.no_vulture:
        if not _module_available(python, "vulture"):
            print(
                f"vulture is not installed for {python!r}. Install it in your venv, e.g.\n"
                f"  {shlex.quote(python)} -m pip install vulture\n"
            )
        else:
            vulture_txt_path = out_dir / "vulture.txt"
            cmd = [
                python,
                "-m",
                "vulture",
                *[str(p) for p in sources],
                "--min-confidence",
                str(args.min_confidence),
                "--exclude",
                ",".join(args.vulture_exclude),
            ]
            print("\n== vulture ==")
            print("$ " + " ".join(shlex.quote(x) for x in cmd))
            res = subprocess.run(
                cmd,
                cwd=str(project_root),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            vulture_txt_path.write_text(res.stdout or "", encoding="utf-8")
            if res.returncode not in (0, 1, 3):
                # vulture returns non-zero when it finds unused code (commonly 1; some builds use 3).
                raise SystemExit(res.returncode)

    report_path = _write_report(
        out_dir=out_dir,
        project_root=project_root,
        sources=sources,
        coverage_json_path=coverage_json_path,
        vulture_txt_path=vulture_txt_path,
    )
    print(f"\nWrote report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
