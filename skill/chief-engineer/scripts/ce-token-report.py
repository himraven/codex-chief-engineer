#!/usr/bin/env python3
"""Report local Codex token use and chief-engineer guardrail drift.

The report opens the Codex state database in read-only mode. It does not upload
data and hides task titles by default. Use --include-titles only when terminal
output may safely contain local task text.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any


DEFAULT_CODEX_HOME = Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser()
CONTEXT_LIMIT = 80_000
TOOL_LIMIT = 40
THREAD_LIMIT = 25_000_000


def local_day(epoch: int) -> str:
    return dt.datetime.fromtimestamp(epoch).strftime("%Y-%m-%d")


def compact(text: str, size: int = 72) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= size else f"{text[:size - 1]}…"


def rollout_metrics(path: str) -> dict[str, int]:
    metrics = {"peak_input": 0, "compactions": 0, "tool_calls": 0}
    rollout = Path(path)
    if not rollout.is_file():
        return metrics
    try:
        with rollout.open(encoding="utf-8") as handle:
            for line in handle:
                event = json.loads(line)
                event_type = event.get("type")
                payload = event.get("payload", {})
                if event_type == "compacted":
                    metrics["compactions"] += 1
                elif event_type == "response_item" and payload.get("type") in {
                    "custom_tool_call",
                    "function_call",
                }:
                    metrics["tool_calls"] += 1
                elif event_type == "event_msg" and payload.get("type") == "token_count":
                    usage = (payload.get("info") or {}).get("last_token_usage") or {}
                    metrics["peak_input"] = max(
                        metrics["peak_input"], int(usage.get("input_tokens") or 0)
                    )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        metrics["unreadable"] = 1
    return metrics


def resolve_root(thread_id: str, parents: dict[str, str]) -> str:
    seen: set[str] = set()
    current = thread_id
    while current in parents and current not in seen:
        seen.add(current)
        current = parents[current]
    return current


def fmt_tokens(value: int) -> str:
    return f"{value / 1_000_000:.1f}M" if value >= 1_000_000 else f"{value:,}"


def direct_run_usage(manifest: dict[str, Any]) -> int:
    usage = manifest.get("usage") or {}

    def safe_int(value: Any) -> int:
        return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0

    return sum(safe_int(usage.get(key)) for key in ("input_tokens", "output_tokens", "reasoning_output_tokens"))


def manifest_text(manifest: dict[str, Any], key: str, default: str) -> str:
    value = manifest.get(key)
    return value if isinstance(value, str) else default


def valid_direct_manifest(manifest: Any) -> bool:
    if not isinstance(manifest, dict) or not isinstance(manifest.get("usage", {}), dict):
        return False
    for key in ("run_id", "requested_model", "reasoning_effort", "budget_state"):
        if key in manifest and not isinstance(manifest[key], str):
            return False
    return all(isinstance(value, int) and not isinstance(value, bool) and value >= 0 for value in (manifest.get("usage") or {}).values())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=dt.datetime.now().strftime("%Y-%m-%d"), help="Local date in YYYY-MM-DD format")
    parser.add_argument("--limit", type=int, default=12, help="Maximum task trees to show")
    parser.add_argument("--codex-home", type=Path, default=DEFAULT_CODEX_HOME, help="Codex state directory")
    parser.add_argument("--include-titles", action="store_true", help="Display local task titles and first prompts")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        dt.date.fromisoformat(args.date)
    except ValueError as exc:
        raise SystemExit(f"Invalid --date {args.date!r}; use YYYY-MM-DD") from exc

    db_path = args.codex_home / "state_5.sqlite"
    if not db_path.is_file():
        raise SystemExit(f"Codex state database is missing: {db_path}")

    columns = "id, rollout_path, created_at, updated_at, tokens_used, model, reasoning_effort"
    if args.include_titles:
        columns += ", title, first_user_message"
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    all_threads = {row["id"]: dict(row) for row in connection.execute(f"SELECT {columns} FROM threads")}
    parents = {row["child_thread_id"]: row["parent_thread_id"] for row in connection.execute("SELECT parent_thread_id, child_thread_id FROM thread_spawn_edges")}
    connection.close()

    today = [row for row in all_threads.values() if local_day(int(row["updated_at"])) == args.date]
    metrics_by_id = {row["id"]: rollout_metrics(row["rollout_path"]) for row in today}
    total_tokens = sum(int(row["tokens_used"] or 0) for row in today)
    direct_run_dir = args.codex_home / "chief-engineer-runs" / args.date
    direct_runs: list[dict[str, Any]] = []
    alerts: list[tuple[str, str]] = []
    if direct_run_dir.is_dir():
        for path in sorted(direct_run_dir.glob("*.manifest.json")):
            try:
                manifest = json.loads(path.read_text(encoding="utf-8"))
                if not valid_direct_manifest(manifest):
                    raise ValueError("invalid direct-run manifest")
                direct_runs.append(manifest)
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
                alerts.append((str(path), "DIRECT_MANIFEST_UNREADABLE"))

    by_model: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: {"sessions": 0, "tokens": 0})
    groups: dict[str, dict[str, Any]] = {}
    for row in today:
        thread_id = row["id"]
        tokens = int(row["tokens_used"] or 0)
        model = row["model"] or "(unknown)"
        effort = row["reasoning_effort"] or "-"
        by_model[(model, effort)]["sessions"] += 1
        by_model[(model, effort)]["tokens"] += tokens
        root_id = resolve_root(thread_id, parents)
        root = all_threads.get(root_id, row)
        label = compact(root.get("title") or root.get("first_user_message") or "(untitled)") if args.include_titles else f"thread-{root_id[:12]}"
        group = groups.setdefault(root_id, {"tokens": 0, "sessions": 0, "models": set(), "label": label, "flags": set()})
        group["tokens"] += tokens
        group["sessions"] += 1
        group["models"].add(f"{model}/{effort}")
        metrics = metrics_by_id[thread_id]
        flags: list[str] = []
        if thread_id in parents and "sol" in model.lower():
            flags.append("SOL_CHILD")
        if thread_id in parents and model == "(unknown)":
            flags.append("UNKNOWN_CHILD_MODEL")
        if metrics["peak_input"] > CONTEXT_LIMIT:
            flags.append(f"CONTEXT>{CONTEXT_LIMIT // 1000}K")
        if metrics["compactions"] > 1:
            flags.append("COMPACTION_LOOP")
        if metrics["tool_calls"] > TOOL_LIMIT:
            flags.append(f"TOOL_CHURN>{TOOL_LIMIT}")
        if tokens > THREAD_LIMIT:
            flags.append("LARGE_THREAD")
        if metrics.get("unreadable"):
            flags.append("ROLLOUT_UNREADABLE")
        for flag in flags:
            group["flags"].add(flag)
            alerts.append((thread_id, flag))

    direct_tokens = 0
    for run in direct_runs:
        tokens = direct_run_usage(run)
        direct_tokens += tokens
        model = manifest_text(run, "requested_model", "(unknown)")
        effort = manifest_text(run, "reasoning_effort", "-")
        by_model[(model, effort)]["sessions"] += 1
        by_model[(model, effort)]["tokens"] += tokens
        if run.get("exit_status") != 0:
            alerts.append((manifest_text(run, "run_id", "(direct run)"), "DIRECT_RUN_FAILED"))
        budget_state = manifest_text(run, "budget_state", "within_budget")
        if budget_state != "within_budget":
            alerts.append((manifest_text(run, "run_id", "(direct run)"), budget_state))

    print(f"# Codex token report — {args.date}")
    print(f"Recorded sessions: {len(today)} | Tokens: {fmt_tokens(total_tokens)}")
    print(f"Direct ephemeral runs: {len(direct_runs)} | Tokens: {fmt_tokens(direct_tokens)}")
    print("\n## By model\n\n| Model / effort | Sessions | Tokens |\n|---|---:|---:|")
    for (model, effort), values in sorted(by_model.items(), key=lambda item: item[1]["tokens"], reverse=True):
        print(f"| {model} / {effort} | {values['sessions']} | {fmt_tokens(values['tokens'])} |")
    print("\n## Largest task trees\n\n| Task tree | Sessions | Tokens | Models | Alerts |\n|---|---:|---:|---|---|")
    for group in sorted(groups.values(), key=lambda value: value["tokens"], reverse=True)[: args.limit]:
        print(f"| {group['label']} | {group['sessions']} | {fmt_tokens(group['tokens'])} | {compact(', '.join(sorted(group['models'])), 58)} | {', '.join(sorted(group['flags'])) or '-'} |")
    if alerts:
        print(f"\n## Gate: BLOCKED ({len(alerts)} alerts)\n\nAlert types: {', '.join(sorted({flag for _, flag in alerts}))}")
        print("Reslice or record an explicit exception before the next chief-engineer wave.")
        return 2
    print("\n## Gate: clear")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
