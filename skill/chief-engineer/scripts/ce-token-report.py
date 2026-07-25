#!/usr/bin/env python3
"""Report exact daily Codex usage and chief-engineer lifecycle health.

The report reads local Codex rollouts and manifests without modifying them.
Task titles stay hidden unless --include-titles is explicitly supplied.
Reasoning tokens are shown as a subset of output and are never double-counted.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


DEFAULT_CODEX_HOME = Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser()
CONTEXT_LIMIT = 80_000
TOOL_LIMIT = 40
DAILY_THREAD_LIMIT = 25_000_000
COMPACTION_ADVISORY = 2
FANOUT_LIMIT = 2
WRITE_ROLES = {"mechanic", "worker", "senior"}
VALID_ROLES = WRITE_ROLES | {"scout", "reviewer"}
LIFECYCLE_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
FINGERPRINT_PATTERN = re.compile(r"[0-9a-f]{64}")

USAGE_KEYS = (
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "unclassified_tokens",
    "total_tokens",
    "turns",
)


def empty_usage() -> dict[str, int]:
    return {key: 0 for key in USAGE_KEYS}


def add_usage(target: dict[str, int], source: dict[str, int]) -> None:
    for key in USAGE_KEYS:
        target[key] += source.get(key, 0)


def safe_int(value: Any) -> int:
    return (
        value
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0
        else 0
    )


def event_local_day(timestamp: Any) -> str | None:
    if not isinstance(timestamp, str):
        return None
    try:
        parsed = dt.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone().date().isoformat()


def day_bounds(date_text: str) -> tuple[int, int]:
    day = dt.date.fromisoformat(date_text)
    start = dt.datetime.combine(day, dt.time.min).astimezone()
    end = dt.datetime.combine(day + dt.timedelta(days=1), dt.time.min).astimezone()
    return int(start.timestamp()), int(end.timestamp())


def compact(text: str, size: int = 72) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= size else f"{text[: size - 1]}…"


def normalized_turn_usage(raw: dict[str, Any]) -> dict[str, int]:
    usage = empty_usage()
    usage["input_tokens"] = safe_int(raw.get("input_tokens"))
    usage["cached_input_tokens"] = min(
        usage["input_tokens"], safe_int(raw.get("cached_input_tokens"))
    )
    usage["output_tokens"] = safe_int(raw.get("output_tokens"))
    usage["reasoning_output_tokens"] = min(
        usage["output_tokens"], safe_int(raw.get("reasoning_output_tokens"))
    )
    classified = usage["input_tokens"] + usage["output_tokens"]
    reported_total = safe_int(raw.get("total_tokens"))
    usage["unclassified_tokens"] = max(0, reported_total - classified)
    usage["total_tokens"] = classified + usage["unclassified_tokens"]
    usage["turns"] = 1 if usage["total_tokens"] else 0
    return usage


def rollout_metrics(path: str, target_date: str) -> dict[str, Any]:
    metrics: dict[str, Any] = {
        "usage": empty_usage(),
        "peak_input": 0,
        "high_context_turns": 0,
        "compactions": 0,
        "lifetime_compactions": 0,
        "tool_calls": 0,
        "unreadable": False,
    }
    rollout = Path(path)
    if not rollout.is_file():
        metrics["unreadable"] = True
        return metrics

    try:
        with rollout.open(encoding="utf-8") as handle:
            for line in handle:
                event = json.loads(line)
                event_type = event.get("type")
                payload = event.get("payload") or {}
                is_target_day = event_local_day(event.get("timestamp")) == target_date

                if event_type == "compacted":
                    metrics["lifetime_compactions"] += 1
                    if is_target_day:
                        metrics["compactions"] += 1
                    continue
                if not is_target_day:
                    continue
                if event_type == "response_item" and payload.get("type") in {
                    "custom_tool_call",
                    "function_call",
                }:
                    metrics["tool_calls"] += 1
                if event_type != "event_msg" or payload.get("type") != "token_count":
                    continue
                info = payload.get("info") or {}
                raw_usage = info.get("last_token_usage") or {}
                turn = normalized_turn_usage(raw_usage)
                if not turn["turns"]:
                    continue
                add_usage(metrics["usage"], turn)
                metrics["peak_input"] = max(metrics["peak_input"], turn["input_tokens"])
                if turn["input_tokens"] > CONTEXT_LIMIT:
                    metrics["high_context_turns"] += 1
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        metrics["unreadable"] = True
    return metrics


def resolve_root(thread_id: str, parents: dict[str, str]) -> str:
    seen: set[str] = set()
    current = thread_id
    while current in parents and current not in seen:
        seen.add(current)
        current = parents[current]
    return current


def fmt_tokens(value: int) -> str:
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    return f"{value:,}"


def direct_run_usage(manifest: dict[str, Any]) -> dict[str, int]:
    return normalized_turn_usage(manifest.get("usage") or {})


def manifest_text(manifest: dict[str, Any], key: str, default: str) -> str:
    value = manifest.get(key)
    return value if isinstance(value, str) and value else default


def valid_direct_manifest(manifest: Any) -> bool:
    if not isinstance(manifest, dict) or not isinstance(manifest.get("usage"), dict):
        return False
    for key in ("run_id", "requested_model", "reasoning_effort", "budget_state"):
        if not isinstance(manifest.get(key), str) or not manifest[key]:
            return False
    for key in ("exit_status", "started_at_epoch", "finished_at_epoch"):
        if (
            not isinstance(manifest.get(key), int)
            or isinstance(manifest[key], bool)
            or manifest[key] < 0
        ):
            return False
    return bool(manifest["usage"]) and all(
        isinstance(value, int) and not isinstance(value, bool) and value >= 0
        for value in manifest["usage"].values()
    )


def valid_gate_manifest(manifest: dict[str, Any]) -> bool:
    for key in ("objective_id", "phase_id", "workstream_id"):
        value = manifest.get(key)
        if not isinstance(value, str) or not LIFECYCLE_ID_PATTERN.fullmatch(value):
            return False
    if manifest.get("role") not in VALID_ROLES:
        return False
    fingerprint = manifest.get("input_fingerprint")
    if not isinstance(fingerprint, str) or not FINGERPRINT_PATTERN.fullmatch(
        fingerprint
    ):
        return False
    return manifest["finished_at_epoch"] >= manifest["started_at_epoch"]


def read_manifests(
    paths: Iterable[Path],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    manifests: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for path in paths:
        objective_id = ""
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(manifest, dict):
                objective_id = manifest_text(manifest, "objective_id", "")
            if not valid_direct_manifest(manifest):
                raise ValueError("invalid direct-run manifest")
            manifest["_manifest_path"] = str(path)
            manifests.append(manifest)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
            errors.append({"path": str(path), "objective_id": objective_id})
    return manifests, errors


def maximum_overlap(manifests: Iterable[dict[str, Any]]) -> int:
    events: list[tuple[int, int]] = []
    for manifest in manifests:
        start = safe_int(manifest.get("started_at_epoch"))
        finish = safe_int(manifest.get("finished_at_epoch"))
        if not start or finish < start:
            continue
        finish = max(finish, start + 1)
        events.append((start, 1))
        events.append((finish, -1))
    current = 0
    peak = 0
    for _, delta in sorted(events, key=lambda item: (item[0], item[1])):
        current += delta
        peak = max(peak, current)
    return peak


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--date",
        default=dt.datetime.now().astimezone().date().isoformat(),
        help="Local date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--limit", type=int, default=12, help="Maximum task trees to show"
    )
    parser.add_argument(
        "--codex-home",
        type=Path,
        default=DEFAULT_CODEX_HOME,
        help="Codex state directory",
    )
    parser.add_argument(
        "--include-titles",
        action="store_true",
        help="Display local task titles and first prompts",
    )
    parser.add_argument(
        "--objective-id",
        help="Evaluate the blocking dispatch gate only for this objective",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        start_epoch, end_epoch = day_bounds(args.date)
    except ValueError as exc:
        raise SystemExit(f"Invalid --date {args.date!r}; use YYYY-MM-DD") from exc
    if args.limit < 1:
        raise SystemExit("--limit must be at least 1")

    db_path = args.codex_home / "state_5.sqlite"
    if not db_path.is_file():
        raise SystemExit(f"Codex state database is missing: {db_path}")

    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    thread_columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(threads)")
    }
    required_columns = {
        "id",
        "rollout_path",
        "created_at",
        "updated_at",
        "model",
        "reasoning_effort",
    }
    missing_columns = sorted(required_columns - thread_columns)
    if missing_columns:
        raise SystemExit(
            "Codex state database is missing required thread columns: "
            + ", ".join(missing_columns)
        )
    title_column = "title" if "title" in thread_columns else "NULL AS title"
    prompt_column = (
        "first_user_message"
        if "first_user_message" in thread_columns
        else "NULL AS first_user_message"
    )
    columns = (
        "id, rollout_path, created_at, updated_at, model, "
        f"reasoning_effort, {title_column}, {prompt_column}"
    )
    all_threads = {
        row["id"]: dict(row)
        for row in connection.execute(f"SELECT {columns} FROM threads")
    }
    table_names = {
        row["name"]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    parents = {}
    if "thread_spawn_edges" in table_names:
        parents = {
            row["child_thread_id"]: row["parent_thread_id"]
            for row in connection.execute(
                "SELECT parent_thread_id, child_thread_id FROM thread_spawn_edges"
            )
        }
    connection.close()

    candidates = [
        row
        for row in all_threads.values()
        if int(row["created_at"] or 0) < end_epoch
        and int(row["updated_at"] or 0) >= start_epoch
        and row.get("rollout_path")
    ]
    metrics_by_id = {
        row["id"]: rollout_metrics(row["rollout_path"], args.date) for row in candidates
    }
    active = [
        row
        for row in candidates
        if metrics_by_id[row["id"]]["usage"]["turns"]
        or metrics_by_id[row["id"]]["compactions"]
        or metrics_by_id[row["id"]]["tool_calls"]
        or metrics_by_id[row["id"]]["unreadable"]
    ]

    by_model: dict[tuple[str, str], dict[str, Any]] = defaultdict(
        lambda: {"sessions": 0, "usage": empty_usage()}
    )
    groups: dict[str, dict[str, Any]] = {}
    advisory_flags: set[str] = set()
    for row in active:
        thread_id = row["id"]
        model = row["model"] or "(unknown)"
        effort = row["reasoning_effort"] or "-"
        metrics = metrics_by_id[thread_id]
        by_model[(model, effort)]["sessions"] += 1
        add_usage(by_model[(model, effort)]["usage"], metrics["usage"])

        root_id = resolve_root(thread_id, parents)
        root = all_threads.get(root_id, row)
        label = (
            compact(root.get("title") or root.get("first_user_message") or "(untitled)")
            if args.include_titles
            else f"task-{root_id[:12]}"
        )
        group = groups.setdefault(
            root_id,
            {
                "usage": empty_usage(),
                "sessions": 0,
                "models": set(),
                "label": label,
                "flags": set(),
            },
        )
        group["sessions"] += 1
        group["models"].add(f"{model}/{effort}")
        add_usage(group["usage"], metrics["usage"])

        flags: list[str] = []
        if thread_id in parents and "sol" in model.lower():
            flags.append("SOL_CHILD")
        if thread_id in parents and model == "(unknown)":
            flags.append("UNKNOWN_CHILD_MODEL")
        if metrics["compactions"] >= COMPACTION_ADVISORY:
            flags.append(f"COMPACTIONS={metrics['compactions']}")
        if metrics["lifetime_compactions"] >= COMPACTION_ADVISORY:
            flags.append(f"LIFETIME_COMPACTIONS={metrics['lifetime_compactions']}")
        if metrics["high_context_turns"]:
            flags.append(f"HIGH_CONTEXT_TURNS={metrics['high_context_turns']}")
        if metrics["tool_calls"] > TOOL_LIMIT:
            flags.append(f"TOOL_CHURN>{TOOL_LIMIT}")
        if metrics["usage"]["total_tokens"] > DAILY_THREAD_LIMIT:
            flags.append("HEAVY_DAILY_USAGE")
        if metrics["unreadable"]:
            flags.append("ROLLOUT_UNREADABLE")
        for flag in flags:
            group["flags"].add(flag)
            advisory_flags.add(flag.split("=")[0])

    direct_run_dir = args.codex_home / "chief-engineer-runs" / args.date
    direct_paths = (
        sorted(direct_run_dir.glob("*.manifest.json"))
        if direct_run_dir.is_dir()
        else []
    )
    direct_runs, direct_errors = read_manifests(direct_paths)
    all_manifest_paths = (
        sorted((args.codex_home / "chief-engineer-runs").glob("*/*.manifest.json"))
        if (args.codex_home / "chief-engineer-runs").is_dir()
        else []
    )
    all_runs, _ = read_manifests(all_manifest_paths)

    fingerprints: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for run in all_runs:
        fingerprint = manifest_text(run, "input_fingerprint", "")
        if valid_gate_manifest(run) and safe_int(run.get("exit_status")) == 0:
            fingerprints[fingerprint].append(run)

    blocking: list[str] = []
    direct_notes: set[str] = set()
    phase_groups: dict[tuple[str, str], dict[str, Any]] = {}
    for error in direct_errors:
        if args.objective_id and error["objective_id"] == args.objective_id:
            blocking.append(f"DIRECT_MANIFEST_INVALID:{Path(error['path']).name}")
        else:
            direct_notes.add("OUT_OF_SCOPE_OR_UNATTRIBUTED_MANIFEST_ERROR")
    for run in direct_runs:
        run_id = manifest_text(run, "run_id", "(direct run)")
        if run.get("observed_model") is None:
            direct_notes.add("OBSERVED_MODEL_UNAVAILABLE")

        objective = manifest_text(run, "objective_id", "(untracked objective)")
        phase = manifest_text(run, "phase_id", "(untracked phase)")
        workstream = manifest_text(run, "workstream_id", "(untracked workstream)")
        in_gate_scope = bool(args.objective_id and objective == args.objective_id)
        if in_gate_scope and not valid_gate_manifest(run):
            blocking.append(
                f"DIRECT_MANIFEST_INVALID:{Path(run['_manifest_path']).name}"
            )
            continue
        if safe_int(run.get("exit_status")) != 0:
            if in_gate_scope:
                blocking.append(f"DIRECT_RUN_FAILED:{run_id}")
            else:
                direct_notes.add("OUT_OF_SCOPE_DIRECT_FAILURE")
        budget_state = manifest_text(run, "budget_state", "within_budget")
        if budget_state != "within_budget":
            if in_gate_scope:
                blocking.append(f"{budget_state}:{run_id}")
            else:
                direct_notes.add("OUT_OF_SCOPE_BUDGET_ALERT")
        if "(untracked" in f"{objective}{phase}{workstream}":
            direct_notes.add("LIFECYCLE_IDS_MISSING")
        phase_group = phase_groups.setdefault(
            (objective, phase),
            {
                "runs": [],
                "write_runs": [],
                "usage": empty_usage(),
                "workstreams": set(),
            },
        )
        phase_group["runs"].append(run)
        if manifest_text(run, "role", "") in WRITE_ROLES:
            phase_group["write_runs"].append(run)
        phase_group["workstreams"].add(workstream)
        add_usage(phase_group["usage"], direct_run_usage(run))

        fingerprint = manifest_text(run, "input_fingerprint", "")
        successful_matches = sorted(
            fingerprints.get(fingerprint, []),
            key=lambda item: (
                safe_int(item.get("started_at_epoch")),
                manifest_text(item, "run_id", ""),
            ),
        )
        is_repeat = (
            len(successful_matches) > 1
            and manifest_text(successful_matches[0], "run_id", "") != run_id
        )
        if is_repeat and in_gate_scope:
            if manifest_text(run, "repeat_reason", ""):
                direct_notes.add("JUSTIFIED_REPEAT")
            else:
                blocking.append(f"UNCHANGED_SUCCESSFUL_REPEAT:{run_id}")
        elif is_repeat:
            direct_notes.add("OUT_OF_SCOPE_REPEAT")

    for (objective, phase), group in phase_groups.items():
        overlap = maximum_overlap(group["runs"])
        write_overlap = maximum_overlap(group["write_runs"])
        group["peak_concurrency"] = overlap
        group["peak_write_concurrency"] = write_overlap
        if write_overlap > FANOUT_LIMIT and args.objective_id == objective:
            blocking.append(
                f"CONCURRENT_WRITE_FANOUT>{FANOUT_LIMIT}:{objective}/{phase}"
            )
        elif write_overlap > FANOUT_LIMIT:
            direct_notes.add("OUT_OF_SCOPE_WRITE_FANOUT_ALERT")

    total_usage = empty_usage()
    for values in by_model.values():
        add_usage(total_usage, values["usage"])
    direct_usage = empty_usage()
    for run in direct_runs:
        add_usage(direct_usage, direct_run_usage(run))

    print(f"# Codex usage and lifecycle report — {args.date}")
    print()
    print(
        f"Active tasks: {len(active)} | Exact daily turns: {total_usage['turns']} | "
        f"Tokens: {fmt_tokens(total_usage['total_tokens'])}"
    )
    print(
        f"Input: {fmt_tokens(total_usage['input_tokens'])} "
        f"({fmt_tokens(total_usage['cached_input_tokens'])} cached / "
        f"{fmt_tokens(total_usage['input_tokens'] - total_usage['cached_input_tokens'])} uncached) | "
        f"Output: {fmt_tokens(total_usage['output_tokens'])} "
        f"(reasoning subset: {fmt_tokens(total_usage['reasoning_output_tokens'])})"
    )
    print(
        f"Direct ephemeral runs: {len(direct_runs)} | "
        f"Tokens: {fmt_tokens(direct_usage['total_tokens'])}"
    )

    print("\n## By model\n")
    print(
        "| Model / effort | Tasks | Total | Input | Cached | Uncached | Output | Reasoning* |"
    )
    print("|---|---:|---:|---:|---:|---:|---:|---:|")
    ranked_models = sorted(
        by_model.items(),
        key=lambda item: item[1]["usage"]["total_tokens"],
        reverse=True,
    )
    for (model, effort), values in ranked_models:
        usage = values["usage"]
        print(
            f"| {model} / {effort} | {values['sessions']} | "
            f"{fmt_tokens(usage['total_tokens'])} | {fmt_tokens(usage['input_tokens'])} | "
            f"{fmt_tokens(usage['cached_input_tokens'])} | "
            f"{fmt_tokens(usage['input_tokens'] - usage['cached_input_tokens'])} | "
            f"{fmt_tokens(usage['output_tokens'])} | "
            f"{fmt_tokens(usage['reasoning_output_tokens'])} |"
        )
    print("\n\\* Reasoning is already included in output; it is not added again.")

    print("\n## Largest task trees\n")
    print("| Task tree | Tasks | Daily tokens | Models | Session-health advisory |")
    print("|---|---:|---:|---|---|")
    ranked_groups = sorted(
        groups.values(), key=lambda value: value["usage"]["total_tokens"], reverse=True
    )
    for group in ranked_groups[: args.limit]:
        print(
            f"| {group['label']} | {group['sessions']} | "
            f"{fmt_tokens(group['usage']['total_tokens'])} | "
            f"{compact(', '.join(sorted(group['models'])), 58)} | "
            f"{', '.join(sorted(group['flags'])) or '-'} |"
        )

    if phase_groups:
        print("\n## Chief phases\n")
        print("| Objective / phase | Runs | Workstreams | Peak all / write | Tokens |")
        print("|---|---:|---:|---:|---:|")
        for (objective, phase), group in sorted(phase_groups.items()):
            print(
                f"| {objective} / {phase} | {len(group['runs'])} | "
                f"{len(group['workstreams'])} | {group['peak_concurrency']} / "
                f"{group['peak_write_concurrency']} | "
                f"{fmt_tokens(group['usage']['total_tokens'])} |"
            )

    print("\n## Interpretation\n")
    if advisory_flags:
        print(
            "Session-health advisories: "
            + ", ".join(sorted(advisory_flags))
            + ". These inform a phase rollover; they do not create tasks or block unrelated work."
        )
    else:
        print("No session-health advisories for active tasks.")
    if direct_notes:
        print("Direct-run notes: " + ", ".join(sorted(direct_notes)) + ".")
    if not args.objective_id:
        print(
            "\n## Current dispatch gate: not evaluated "
            "(pass --objective-id to scope it)"
        )
        return 0
    if blocking:
        print(f"\n## Current dispatch gate: BLOCKED ({len(blocking)})\n")
        for alert in sorted(set(blocking)):
            print(f"- {alert}")
        return 2
    print("\n## Current dispatch gate: clear")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
