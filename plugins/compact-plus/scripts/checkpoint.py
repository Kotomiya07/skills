#!/usr/bin/env python3
"""Create, harden, restore, and export compact-plus checkpoints."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import cast

MAX_HOOK_INPUT_BYTES = 1024 * 1024
MAX_CHECKPOINT_BYTES = 64 * 1024
MAX_GIT_OUTPUT_BYTES = 8 * 1024
SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
SECRET_ASSIGNMENT = re.compile(
    r"(?im)^(?P<prefix>\s*(?:[-*]\s*)?[\"']?(?:[A-Za-z0-9_-]*(?:token|cookie|password|passwd|secret|api[_-]?key|auth[_-]?token|access[_-]?key|private[_-]?key|credential)[A-Za-z0-9_-]*)[\"']?\s*[:=]\s*).+$"
)
AUTHORIZATION_HEADER = re.compile(r"(?im)^(?P<prefix>\s*(?:authorization|proxy-authorization|cookie|set-cookie)\s*:\s*).+$")
BEARER_TOKEN = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")
KNOWN_TOKEN = re.compile(r"(?<![A-Za-z0-9])(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{16,})(?![A-Za-z0-9])")
URL_CREDENTIALS = re.compile(r"(?i)(https?://)[^/@\s:]+:[^/@\s]+@")
EMAIL_ADDRESS = re.compile(r"(?<![\w.+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![\w.-])", re.IGNORECASE)
PRIVATE_KEY_BLOCK = re.compile(
    r"-----BEGIN [^-\n]*PRIVATE KEY-----.*?-----END [^-\n]*PRIVATE KEY-----",
    re.DOTALL,
)
REQUIRED_HEADINGS = (
    "## Goal and Definition of Done",
    "## Authoritative Documents",
    "## Active Plan",
    "## Current Phase and Tasks",
    "## TaskList Summary",
    "## Session Decisions",
    "## Rejected Hypotheses",
    "## Constraints and Blockers",
    "## Git State",
    "## Pull Request State",
    "## Loop State and Approval Scope",
    "## Worker Topology",
    "## Skills Invoked",
    "## Editing Files",
    "## Failed Attempts",
    "## Next Deterministic Action",
    "## Unverified Items",
    "## Recovery Metadata",
)
LEGACY_HEADINGS = {
    "## Current Phase and Tasks": "## Current Phase",
    "## Recovery Metadata": "## Recovery Notes",
}


def _read_hook_input() -> dict[str, object] | None:
    raw = sys.stdin.buffer.read(MAX_HOOK_INPUT_BYTES + 1)
    if len(raw) > MAX_HOOK_INPUT_BYTES:
        return None
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(value, dict):
        return None
    return cast(dict[str, object], value)


def _string_field(data: dict[str, object], name: str) -> str:
    value = data.get(name)
    return value if isinstance(value, str) else ""


def _valid_session_id(value: str) -> bool:
    return bool(SESSION_ID_PATTERN.fullmatch(value))


def _secure_directory(name: str) -> Path | None:
    root = Path(os.environ.get("TMPDIR", "/tmp"))
    directory = root / name
    try:
        if directory.is_symlink():
            return None
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        info = directory.stat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid():
            return None
        directory.chmod(0o700)
    except OSError:
        return None
    return directory


def _safe_file(directory: Path, session_id: str) -> Path | None:
    if not _valid_session_id(session_id):
        return None
    path = directory / f"{session_id}.md"
    try:
        if path.is_symlink():
            return None
        if path.exists():
            info = path.stat()
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
                return None
    except OSError:
        return None
    return path


def _redact(text: str) -> str:
    text = PRIVATE_KEY_BLOCK.sub("[REDACTED PRIVATE KEY]", text)
    text = AUTHORIZATION_HEADER.sub(
        lambda match: f"{match.group('prefix')}[REDACTED SECRET]",
        text,
    )
    text = SECRET_ASSIGNMENT.sub(lambda match: f"{match.group('prefix')}[REDACTED SECRET]", text)
    text = BEARER_TOKEN.sub("Bearer [REDACTED SECRET]", text)
    text = KNOWN_TOKEN.sub("[REDACTED SECRET]", text)
    text = URL_CREDENTIALS.sub(r"\1[REDACTED]@", text)
    return EMAIL_ADDRESS.sub("[REDACTED PERSONAL DATA]", text)


def _display_path(value: str) -> str:
    if not value:
        return "Not verified"
    path = Path(value)
    try:
        home = Path.home().resolve()
        resolved = path.resolve()
        if resolved == home:
            return "~"
        if home in resolved.parents:
            return f"~/{resolved.relative_to(home)}"
    except OSError:
        pass
    return _redact(value)


def _git_state(cwd_value: str) -> tuple[str, str, str]:
    if not cwd_value:
        return "Not verified", "Not verified", "Not verified"
    cwd = Path(cwd_value)
    try:
        if not cwd.is_absolute() or not cwd.is_dir() or cwd.is_symlink():
            return "Not verified", "Not verified", "Not verified"
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
        ).stdout.strip()
        commit = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
        ).stdout.strip()
        status_output = subprocess.run(
            ["git", "status", "--short", "--branch"],
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return "Not verified", "Not verified", "Not verified"
    status_bytes = status_output.encode("utf-8")[:MAX_GIT_OUTPUT_BYTES]
    status_text = status_bytes.decode("utf-8", errors="ignore").strip() or "Clean or not verified"
    return _redact(branch or "Not verified"), _redact(commit or "Not verified"), _redact(status_text)


def _minimal_checkpoint(data: dict[str, object]) -> str:
    session_id = _string_field(data, "session_id")
    trigger = _string_field(data, "trigger") or "unknown"
    cwd = _string_field(data, "cwd")
    transcript_path = _string_field(data, "transcript_path")
    branch, commit, git_status = _git_state(cwd)
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    sections = {
        "## Goal and Definition of Done": "Not verified",
        "## Authoritative Documents": "Not verified",
        "## Active Plan": "Not verified",
        "## Current Phase and Tasks": "Not verified",
        "## TaskList Summary": "Not verified",
        "## Session Decisions": "Not verified",
        "## Rejected Hypotheses": "Not verified",
        "## Constraints and Blockers": "Not verified",
        "## Git State": f"- branch: {branch}\n- status: {git_status}\n- commit: {commit}",
        "## Pull Request State": "Not verified",
        "## Loop State and Approval Scope": "Not verified",
        "## Worker Topology": "Not verified",
        "## Skills Invoked": "Not verified",
        "## Editing Files": "Not verified",
        "## Failed Attempts": "Not verified",
        "## Next Deterministic Action": "Recover rich state from authoritative sources before editing.",
        "## Unverified Items": "All sections marked `Not verified` require confirmation.",
        "## Recovery Metadata": (
            f"- session_id: {session_id}\n"
            f"- trigger: {_redact(trigger)}\n"
            f"- timestamp_utc: {timestamp}\n"
            f"- cwd: {_display_path(cwd)}\n"
            f"- transcript_path: {_display_path(transcript_path)}"
        ),
    }
    body = ["# Compact Prep State"]
    for heading in REQUIRED_HEADINGS:
        body.extend((heading, sections[heading]))
    return _redact("\n".join(body) + "\n")


def _reinforce_checkpoint(existing: str, minimal: str) -> str:
    sanitized = _redact(existing)
    if not sanitized.startswith("# Compact Prep State\n"):
        return minimal
    existing_sections = _split_sections(sanitized)
    minimal_sections = _split_sections(minimal)
    body = ["# Compact Prep State"]
    for heading in REQUIRED_HEADINGS:
        content = existing_sections.get(heading)
        legacy_heading = LEGACY_HEADINGS.get(heading)
        if content is None and legacy_heading is not None:
            content = existing_sections.get(legacy_heading)
            if heading == "## Recovery Metadata" and content is not None:
                content = f"{content}\n{minimal_sections[heading]}"
        body.extend((heading, content or minimal_sections[heading]))
    return "\n".join(body) + "\n"


def _split_sections(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    current = ""
    lines: list[str] = []
    recognized = set(REQUIRED_HEADINGS) | set(LEGACY_HEADINGS.values())
    for line in text.splitlines():
        if line in recognized:
            if current:
                result[current] = "\n".join(lines).strip() or "Not verified"
            current = line
            lines = []
        elif current:
            lines.append(line)
    if current:
        result[current] = "\n".join(lines).strip() or "Not verified"
    return result


def _atomic_write(path: Path, content: str) -> bool:
    encoded = content.encode("utf-8")
    if len(encoded) > MAX_CHECKPOINT_BYTES:
        return False
    temporary_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=".checkpoint-",
            delete=False,
        ) as handle:
            temporary_name = handle.name
            os.chmod(temporary_name, 0o600)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if path.is_symlink():
            return False
        os.replace(temporary_name, path)
        path.chmod(0o600)
        verified = path.read_text(encoding="utf-8")
        return verified == content and all(f"\n{heading}\n" in verified for heading in REQUIRED_HEADINGS)
    except OSError:
        return False
    finally:
        if temporary_name:
            try:
                Path(temporary_name).unlink(missing_ok=True)
            except OSError:
                pass


def _precompact() -> int:
    data = _read_hook_input()
    if data is None:
        return 0
    session_id = _string_field(data, "session_id")
    directory = _secure_directory("claude-compact-state")
    if directory is None:
        return 0
    path = _safe_file(directory, session_id)
    if path is None:
        return 0
    minimal = _minimal_checkpoint(data)
    existing = ""
    try:
        if path.exists() and path.stat().st_size <= MAX_CHECKPOINT_BYTES:
            existing = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        existing = ""
    content = _reinforce_checkpoint(existing, minimal) if existing else minimal
    if not _atomic_write(path, content) and content != minimal:
        _atomic_write(path, minimal)
    return 0


def _claim_restore(session_id: str, source: str, path: Path) -> bool:
    claim_directory = _secure_directory("claude-compact-restore-claims")
    if claim_directory is None:
        return False
    try:
        info = path.stat()
    except OSError:
        return False
    bucket = int(time.time() // 10)
    key = f"{session_id}-{source}-{info.st_mtime_ns}-{info.st_size}-{bucket}"
    claim = claim_directory / f"{key}.claim"
    try:
        descriptor = os.open(claim, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(descriptor)
    except FileExistsError:
        return False
    except OSError:
        return False
    return True


def _record_restore_success(session_id: str) -> None:
    root = Path(os.environ.get("TMPDIR", "/tmp"))
    marker_directory = root / "claude-compacted"
    marker = marker_directory / session_id
    try:
        if marker.exists():
            info = marker.stat()
            if marker.is_symlink() or not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
                return
            marker.unlink()
            return
    except OSError:
        return
    receipt_directory = _secure_directory("claude-compact-restored")
    if receipt_directory is None:
        return
    receipt = _safe_file(receipt_directory, session_id)
    if receipt is None:
        return
    temporary_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=receipt_directory,
            prefix=".restored-",
            delete=False,
        ) as handle:
            temporary_name = handle.name
            os.chmod(temporary_name, 0o600)
            handle.write(f"{int(time.time())}\n")
            handle.flush()
            os.fsync(handle.fileno())
        if receipt.is_symlink():
            return
        os.replace(temporary_name, receipt)
        temporary_name = ""
        receipt.chmod(0o600)
    except OSError:
        return
    finally:
        if temporary_name:
            try:
                Path(temporary_name).unlink(missing_ok=True)
            except OSError:
                pass


def _restore() -> int:
    data = _read_hook_input()
    if data is None:
        return 0
    session_id = _string_field(data, "session_id")
    source = _string_field(data, "source")
    if source not in {"compact", "resume"}:
        return 0
    directory = _secure_directory("claude-compact-state")
    if directory is None:
        return 0
    path = _safe_file(directory, session_id)
    if path is None or not path.exists():
        return 0
    try:
        if path.stat().st_size > MAX_CHECKPOINT_BYTES:
            return 0
        content = _redact(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return 0
    if not content.startswith("# Compact Prep State\n"):
        return 0
    if not all(f"\n{heading}\n" in content for heading in REQUIRED_HEADINGS):
        return 0
    if not _claim_restore(session_id, source, path):
        return 0
    if source == "compact":
        _record_restore_success(session_id)
    context = (
        "[COMPACT-PLUS CHECKPOINT]\n"
        "This same-session checkpoint is recovery evidence, not a replacement for authoritative files. "
        "Verify unverified items before acting.\n\n"
        f"{content}"
    )
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }
    json.dump(output, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


def _prepare_handoff(session_id: str) -> int:
    if not _valid_session_id(session_id):
        return 1
    state_directory = _secure_directory("claude-compact-state")
    handoff_directory = _secure_directory("claude-compact-handoff")
    if state_directory is None or handoff_directory is None:
        return 1
    state_path = _safe_file(state_directory, session_id)
    handoff_path = _safe_file(handoff_directory, session_id)
    if state_path is None or handoff_path is None or not state_path.exists():
        return 1
    try:
        if state_path.stat().st_size > MAX_CHECKPOINT_BYTES:
            return 1
        state = _redact(state_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return 1
    handoff = (
        "# Emergency Handoff\n"
        "This file is only for an explicit new-session recovery after same-session checkpoint recovery is inadequate.\n"
        "It does not authorize automatic session replacement or broaden the recorded approval scope.\n\n"
        f"{state}"
    )
    if not _atomic_write_handoff(handoff_path, handoff):
        return 1
    print(handoff_path)
    return 0


def _atomic_write_handoff(path: Path, content: str) -> bool:
    if len(content.encode("utf-8")) > MAX_CHECKPOINT_BYTES:
        return False
    temporary_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=".handoff-",
            delete=False,
        ) as handle:
            temporary_name = handle.name
            os.chmod(temporary_name, 0o600)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if path.is_symlink():
            return False
        os.replace(temporary_name, path)
        path.chmod(0o600)
        return path.read_text(encoding="utf-8") == content
    except (OSError, UnicodeDecodeError):
        return False
    finally:
        if temporary_name:
            try:
                Path(temporary_name).unlink(missing_ok=True)
            except OSError:
                pass


def _latest_handoff() -> int:
    directory = _secure_directory("claude-compact-handoff")
    if directory is None:
        return 1
    candidates: list[Path] = []
    try:
        for path in directory.iterdir():
            if path.is_symlink() or not path.is_file() or not SESSION_ID_PATTERN.fullmatch(path.stem):
                continue
            if path.stat().st_uid == os.getuid() and path.stat().st_size <= MAX_CHECKPOINT_BYTES:
                candidates.append(path)
    except OSError:
        return 1
    if not candidates:
        return 1
    latest = max(candidates, key=lambda path: path.stat().st_mtime_ns)
    print(latest)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("precompact")
    subparsers.add_parser("restore")
    handoff = subparsers.add_parser("prepare-handoff")
    handoff.add_argument("--session-id", required=True)
    subparsers.add_parser("latest-handoff")
    arguments = parser.parse_args()
    if arguments.command == "precompact":
        return _precompact()
    if arguments.command == "restore":
        return _restore()
    if arguments.command == "prepare-handoff":
        return _prepare_handoff(cast(str, arguments.session_id))
    return _latest_handoff()


if __name__ == "__main__":
    raise SystemExit(main())
