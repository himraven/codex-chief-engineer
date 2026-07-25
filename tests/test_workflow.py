from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sqlite3
import subprocess
import tempfile
import time
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT = REPO_ROOT / "skill/chief-engineer/scripts/ce-token-report.py"
DISPATCH = REPO_ROOT / "skill/chief-engineer/scripts/ce-dispatch.sh"
REPORT_SPEC = importlib.util.spec_from_file_location("ce_token_report", REPORT)
assert REPORT_SPEC and REPORT_SPEC.loader
REPORT_MODULE = importlib.util.module_from_spec(REPORT_SPEC)
REPORT_SPEC.loader.exec_module(REPORT_MODULE)


def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=False,
        text=True,
        capture_output=True,
        **kwargs,
    )


class TokenReportTests(unittest.TestCase):
    def test_day_bounds_localize_both_midnights_across_dst(self) -> None:
        if not hasattr(time, "tzset"):
            self.skipTest("tzset is unavailable")
        previous_timezone = os.environ.get("TZ")
        try:
            os.environ["TZ"] = "America/New_York"
            time.tzset()
            start, end = REPORT_MODULE.day_bounds("2026-11-01")
            self.assertEqual(end - start, 25 * 60 * 60)
        finally:
            if previous_timezone is None:
                os.environ.pop("TZ", None)
            else:
                os.environ["TZ"] = previous_timezone
            time.tzset()

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.codex_home = Path(self.tempdir.name)
        self.day_start, self.day_end = REPORT_MODULE.day_bounds("2026-07-24")
        rollout = self.codex_home / "rollout.jsonl"
        events = [
            {
                "timestamp": "2026-07-23T12:00:00Z",
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "info": {
                        "last_token_usage": {
                            "input_tokens": 1000,
                            "cached_input_tokens": 900,
                            "output_tokens": 10,
                            "reasoning_output_tokens": 4,
                            "total_tokens": 1010,
                        }
                    },
                },
            },
            {
                "timestamp": "2026-07-24T12:00:00Z",
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "info": {
                        "last_token_usage": {
                            "input_tokens": 100,
                            "cached_input_tokens": 80,
                            "output_tokens": 20,
                            "reasoning_output_tokens": 5,
                            "total_tokens": 120,
                        }
                    },
                },
            },
            {
                "timestamp": "2026-07-24T12:01:00Z",
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "info": {
                        "last_token_usage": {
                            "input_tokens": 0,
                            "cached_input_tokens": 0,
                            "output_tokens": 0,
                            "reasoning_output_tokens": 0,
                            "total_tokens": 50,
                        }
                    },
                },
            },
            {
                "timestamp": "2026-07-24T12:02:00Z",
                "type": "compacted",
                "payload": {},
            },
            {
                "timestamp": "2026-07-24T12:03:00Z",
                "type": "compacted",
                "payload": {},
            },
        ]
        rollout.write_text(
            "".join(json.dumps(event) + "\n" for event in events), encoding="utf-8"
        )

        database = sqlite3.connect(self.codex_home / "state_5.sqlite")
        database.execute(
            """
            CREATE TABLE threads (
              id TEXT PRIMARY KEY,
              rollout_path TEXT,
              created_at INTEGER,
              updated_at INTEGER,
              model TEXT,
              reasoning_effort TEXT,
              title TEXT,
              first_user_message TEXT
            )
            """
        )
        database.execute(
            "CREATE TABLE thread_spawn_edges (parent_thread_id TEXT, child_thread_id TEXT)"
        )
        database.execute(
            "INSERT INTO threads VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "11111111-1111-1111-1111-111111111111",
                str(rollout),
                1784764800,
                1785024000,
                "gpt-5.6-sol",
                "xhigh",
                "private title",
                "private prompt",
            ),
        )
        database.commit()
        database.close()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def report(
        self,
        objective_id: str | None = None,
        *,
        run_home: Path | None = None,
        env: dict[str, str] | None = None,
        date: str = "2026-07-24",
    ) -> subprocess.CompletedProcess[str]:
        command = [
            "python3",
            str(REPORT),
            "--date",
            date,
            "--codex-home",
            str(self.codex_home),
        ]
        if objective_id is not None:
            command.extend(["--objective-id", objective_id])
        if run_home:
            command.extend(["--run-home", str(run_home)])
        return run(command, env=env)

    def write_manifest(
        self,
        run_id: str,
        *,
        fingerprint: str,
        started: int,
        finished: int,
        repeat_reason: str = "",
        role: str = "worker",
        run_home: Path | None = None,
        exit_status: int = 0,
        index_date: str = "2026-07-24",
    ) -> Path:
        directory = (run_home or self.codex_home / "chief-engineer-runs") / index_date
        directory.mkdir(parents=True, exist_ok=True)
        manifest = {
            "run_id": run_id,
            "objective_id": "OBJ-1",
            "phase_id": "P1",
            "workstream_id": f"WS-{run_id}",
            "role": role,
            "requested_model": "gpt-5.6-luna",
            "reasoning_effort": "low",
            "observed_model": "gpt-5.6-luna",
            "budget_state": "within_budget",
            "exit_status": exit_status,
            "input_fingerprint": hashlib.sha256(fingerprint.encode()).hexdigest(),
            "repeat_reason": repeat_reason,
            "started_at_epoch": self.day_start + started,
            "finished_at_epoch": self.day_start + finished,
            "usage": {
                "input_tokens": 10,
                "cached_input_tokens": 6,
                "output_tokens": 2,
                "reasoning_output_tokens": 1,
                "total_tokens": 12,
            },
        }
        path = directory / f"{run_id}.manifest.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return path

    def test_exact_daily_usage_does_not_double_count_reasoning(self) -> None:
        result = self.report()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Tokens: 170", result.stdout)
        self.assertIn("Input: 100 (80 cached / 20 uncached)", result.stdout)
        self.assertIn("Output: 20 (reasoning subset: 5)", result.stdout)
        self.assertNotIn("Tokens: 1,180", result.stdout)
        self.assertNotIn("private title", result.stdout)
        self.assertIn("Current dispatch gate: not evaluated", result.stdout)
        self.assertIn("do not create tasks or block unrelated work", result.stdout)

    def test_invalid_objective_id_is_rejected(self) -> None:
        result = self.report("OBJ/1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--objective-id must match", result.stderr)

        empty_result = self.report("")
        self.assertNotEqual(empty_result.returncode, 0)
        self.assertIn("--objective-id must match", empty_result.stderr)

    def test_explicit_run_home_matches_dispatch_manifest_index(self) -> None:
        environment_run_home = self.codex_home / "environment-run-index"
        self.write_manifest(
            "failed-run",
            fingerprint="failed",
            started=100,
            finished=110,
            run_home=environment_run_home,
            exit_status=1,
        )
        environment = os.environ.copy()
        environment["CE_RUN_HOME"] = str(environment_run_home)
        result = self.report("OBJ-1", env=environment)
        self.assertEqual(result.returncode, 2)
        self.assertIn("DIRECT_RUN_FAILED:failed-run", result.stdout)
        self.assertIn("| gpt-5.6-luna / low | 1 | 12 |", result.stdout)

        explicit_run_home = self.codex_home / "explicit-run-index"
        override_result = self.report(
            "OBJ-1",
            run_home=explicit_run_home,
            env=environment,
        )
        self.assertEqual(override_result.returncode, 0, override_result.stdout)
        self.assertIn("Current dispatch gate: clear", override_result.stdout)

    def test_relative_environment_run_home_is_rejected(self) -> None:
        environment = os.environ.copy()
        environment["CE_RUN_HOME"] = "relative-run-index"
        result = run(
            [
                "python3",
                str(REPORT),
                "--date",
                "2026-07-24",
                "--codex-home",
                str(self.codex_home),
                "--objective-id",
                "OBJ-1",
            ],
            cwd=self.codex_home,
            env=environment,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "CE_RUN_HOME must resolve to an absolute path",
            result.stderr,
        )

    def test_unreadable_rollout_remains_visible_as_advisory(self) -> None:
        database = sqlite3.connect(self.codex_home / "state_5.sqlite")
        database.execute(
            "INSERT INTO threads VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "22222222-2222-2222-2222-222222222222",
                str(self.codex_home / "missing-rollout.jsonl"),
                1784764800,
                1785024000,
                "gpt-5.6-sol",
                "xhigh",
                "unreadable title",
                "unreadable prompt",
            ),
        )
        database.commit()
        database.close()
        result = self.report()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Active tasks: 2", result.stdout)
        self.assertIn("ROLLOUT_UNREADABLE", result.stdout)

    def test_unjustified_unchanged_repeat_blocks_current_gate(self) -> None:
        self.write_manifest("run-1", fingerprint="same", started=100, finished=110)
        self.write_manifest("run-2", fingerprint="same", started=111, finished=120)
        result = self.report("OBJ-1")
        self.assertEqual(result.returncode, 2)
        self.assertIn("UNCHANGED_SUCCESSFUL_REPEAT:run-2", result.stdout)

    def test_justified_repeat_remains_visible_but_clear(self) -> None:
        self.write_manifest("run-1", fingerprint="same", started=100, finished=110)
        self.write_manifest(
            "run-2",
            fingerprint="same",
            started=111,
            finished=120,
            repeat_reason="new runtime evidence",
        )
        result = self.report("OBJ-1")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("JUSTIFIED_REPEAT", result.stdout)
        self.assertIn("Current dispatch gate: clear", result.stdout)

    def test_blank_repeat_reason_does_not_clear_gate(self) -> None:
        self.write_manifest("run-1", fingerprint="same", started=100, finished=110)
        self.write_manifest(
            "run-2",
            fingerprint="same",
            started=111,
            finished=120,
            repeat_reason="   ",
        )
        result = self.report("OBJ-1")
        self.assertEqual(result.returncode, 2)
        self.assertIn("UNCHANGED_SUCCESSFUL_REPEAT:run-2", result.stdout)
        self.assertNotIn("JUSTIFIED_REPEAT", result.stdout)

    def test_concurrent_fanout_above_two_blocks(self) -> None:
        for index in range(3):
            self.write_manifest(
                f"run-{index}",
                fingerprint=f"fingerprint-{index}",
                started=100,
                finished=120,
            )
        result = self.report("OBJ-1")
        self.assertEqual(result.returncode, 2)
        self.assertIn("CONCURRENT_WRITE_FANOUT>2:OBJ-1/P1", result.stdout)

    def test_cross_midnight_runs_gate_both_days_and_count_on_completion_day(
        self,
    ) -> None:
        for index in range(3):
            self.write_manifest(
                f"cross-midnight-{index}",
                fingerprint=f"cross-midnight-{index}",
                started=-60,
                finished=120,
                index_date="2026-07-23",
            )

        previous_day = self.report("OBJ-1", date="2026-07-23")
        self.assertEqual(previous_day.returncode, 2)
        self.assertIn("CONCURRENT_WRITE_FANOUT>2:OBJ-1/P1", previous_day.stdout)
        self.assertIn(
            "Direct ephemeral completions: 0 | Overlapping runs: 3 | Tokens: 0",
            previous_day.stdout,
        )

        completion_day = self.report("OBJ-1")
        self.assertEqual(completion_day.returncode, 2)
        self.assertIn("CONCURRENT_WRITE_FANOUT>2:OBJ-1/P1", completion_day.stdout)
        self.assertIn(
            "Direct ephemeral completions: 3 | Overlapping runs: 3 | Tokens: 36",
            completion_day.stdout,
        )

    def test_malformed_in_scope_manifest_fails_closed(self) -> None:
        directory = self.codex_home / "chief-engineer-runs/2026-07-24"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "malformed.manifest.json").write_text(
            json.dumps(
                {
                    "run_id": "malformed",
                    "objective_id": "OBJ-1",
                    "requested_model": "gpt-5.6-luna",
                    "reasoning_effort": "low",
                    "budget_state": "within_budget",
                    "usage": {"input_tokens": 10},
                }
            ),
            encoding="utf-8",
        )
        result = self.report("OBJ-1")
        self.assertEqual(result.returncode, 2)
        self.assertIn("DIRECT_MANIFEST_INVALID:malformed.manifest.json", result.stdout)

    def test_unattributed_invalid_json_fails_closed_when_scoped(self) -> None:
        directory = self.codex_home / "chief-engineer-runs/2026-07-24"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "truncated.manifest.json").write_text(
            '{"objective_id":',
            encoding="utf-8",
        )
        result = self.report("OBJ-1")
        self.assertEqual(result.returncode, 2)
        self.assertIn("DIRECT_MANIFEST_INVALID:truncated.manifest.json", result.stdout)

    def test_missing_gate_fields_fail_closed(self) -> None:
        path = self.write_manifest(
            "run-missing-fields",
            fingerprint="missing-fields",
            started=100,
            finished=110,
        )
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest.pop("role")
        manifest.pop("input_fingerprint")
        path.write_text(json.dumps(manifest), encoding="utf-8")
        result = self.report("OBJ-1")
        self.assertEqual(result.returncode, 2)
        self.assertIn(
            "DIRECT_MANIFEST_INVALID:run-missing-fields.manifest.json",
            result.stdout,
        )

    def test_inverted_manifest_timestamps_fail_closed(self) -> None:
        self.write_manifest(
            "run-inverted",
            fingerprint="inverted",
            started=110,
            finished=100,
        )
        result = self.report("OBJ-1")
        self.assertEqual(result.returncode, 2)
        self.assertIn(
            "DIRECT_MANIFEST_INVALID:run-inverted.manifest.json", result.stdout
        )

    def test_read_only_fanout_does_not_block_write_gate(self) -> None:
        for index in range(3):
            self.write_manifest(
                f"run-{index}",
                fingerprint=f"fingerprint-{index}",
                started=100,
                finished=120,
                role="scout",
            )
        result = self.report("OBJ-1")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("| 3 / 0 |", result.stdout)
        self.assertIn("Current dispatch gate: clear", result.stdout)


class DispatchTests(unittest.TestCase):
    def test_dispatch_fingerprints_and_rejects_unchanged_repeat(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = root / "repo"
            repository.mkdir()
            subprocess.run(["git", "init", "-q", str(repository)], check=True)
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repository),
                    "config",
                    "user.email",
                    "test@example.com",
                ],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(repository), "config", "user.name", "Test"],
                check=True,
            )
            (repository / "README.md").write_text("fixture\n", encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(repository), "add", "README.md"], check=True
            )
            subprocess.run(
                ["git", "-C", str(repository), "commit", "-qm", "test fixture"],
                check=True,
            )
            submodule_source = root / "submodule-source"
            submodule_source.mkdir()
            subprocess.run(["git", "init", "-q", str(submodule_source)], check=True)
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(submodule_source),
                    "config",
                    "user.email",
                    "test@example.com",
                ],
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(submodule_source),
                    "config",
                    "user.name",
                    "Test",
                ],
                check=True,
            )
            (submodule_source / "evidence.txt").write_text("clean\n", encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(submodule_source), "add", "evidence.txt"],
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(submodule_source),
                    "commit",
                    "-qm",
                    "submodule fixture",
                ],
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repository),
                    "-c",
                    "protocol.file.allow=always",
                    "submodule",
                    "add",
                    "-q",
                    str(submodule_source),
                    "modules/evidence",
                ],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(repository), "commit", "-qam", "add submodule"],
                check=True,
            )
            linked_worktree = repository / ".worktrees/scout"
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repository),
                    "worktree",
                    "add",
                    "-q",
                    "-b",
                    "test-scout",
                    str(linked_worktree),
                ],
                check=True,
            )
            scratch = repository / "scratch.txt"
            scratch.write_text("untracked v1\n", encoding="utf-8")
            outside_link = repository / "outside-link"
            outside_link.symlink_to("/dev/zero")

            brief = root / "brief.md"
            brief.write_text("# Objective\nInspect the fixture.\n", encoding="utf-8")
            allowlist = root / "allowlist.txt"
            allowlist.write_text(f"{repository}\n", encoding="utf-8")
            fake_bin = root / "bin"
            fake_bin.mkdir()
            fake_codex = fake_bin / "codex"
            fake_codex.write_text(
                """#!/usr/bin/env bash
set -euo pipefail
output=""
cwd=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    -o) output="$2"; shift 2 ;;
    -C) cwd="$2"; shift 2 ;;
    *) shift ;;
  esac
done
cat >/dev/null
if [[ -n "${FAKE_CODEX_UNTRACKED_FILE:-}" ]]; then
  printf 'generated artifact\\n' > "$cwd/$FAKE_CODEX_UNTRACKED_FILE"
fi
if [[ -n "${FAKE_CODEX_COMMIT_CONTENT:-}" ]]; then
  printf '%s\\n' "$FAKE_CODEX_COMMIT_CONTENT" > "$cwd/committed.txt"
  git -C "$cwd" add committed.txt
  git -C "$cwd" -c user.email=test@example.com -c user.name=Test \
    commit -qm "executor fixture"
fi
printf 'fixture result\\n' > "$output"
printf '%s\\n' '{"type":"turn.completed","usage":{"input_tokens":10,"cached_input_tokens":6,"output_tokens":2,"reasoning_output_tokens":1,"total_tokens":12}}'
""",
                encoding="utf-8",
            )
            fake_codex.chmod(0o755)

            environment = os.environ.copy()
            environment.update(
                {
                    "PATH": f"{fake_bin}:{environment['PATH']}",
                    "CE_APPROVED_REPO_ROOTS": str(allowlist),
                    "CE_RUN_HOME": str(root / "run-index"),
                    "CODEX_HOME": str(root / "codex-home"),
                }
            )
            command = [
                "bash",
                str(DISPATCH),
                "--role",
                "scout",
                "--objective-id",
                "OBJ-1",
                "--phase-id",
                "P1",
                "--workstream-id",
                "WS-evidence",
                "--cwd",
                str(repository),
                "--brief",
                str(brief),
                "--result-dir",
                str(root / "results"),
            ]
            linked_result_command = command.copy()
            linked_result_command[linked_result_command.index("--cwd") + 1] = str(
                linked_worktree
            )
            linked_result_command[-1] = str(repository / "linked-results")
            linked_result = run(linked_result_command, env=environment)
            self.assertEqual(linked_result.returncode, 68)
            self.assertIn(
                "Result directory must be outside the repository",
                linked_result.stderr,
            )

            linked_run_environment = environment.copy()
            linked_run_environment["CE_RUN_HOME"] = str(repository / "linked-run-index")
            linked_run_command = linked_result_command.copy()
            linked_run_command[-1] = str(root / "linked-results")
            linked_run = run(linked_run_command, env=linked_run_environment)
            self.assertEqual(linked_run.returncode, 64)
            self.assertIn(
                "Run index must be outside the repository",
                linked_run.stderr,
            )

            inside_result_dir = repository / "run-artifacts"
            inside_result_command = [*command[:-1], str(inside_result_dir)]
            inside_result = run(inside_result_command, env=environment)
            self.assertEqual(inside_result.returncode, 68)
            self.assertIn(
                "Result directory must be outside the repository",
                inside_result.stderr,
            )
            self.assertFalse(inside_result_dir.exists())

            result_alias = root / "result-alias"
            result_alias.symlink_to(inside_result_dir, target_is_directory=True)
            aliased_result_command = [*command[:-1], str(result_alias)]
            aliased_result = run(aliased_result_command, env=environment)
            self.assertEqual(aliased_result.returncode, 68)
            self.assertIn(
                "Result directory must be outside the repository",
                aliased_result.stderr,
            )
            result_alias.unlink()

            repository_result_command = [*command[:-1], str(repository)]
            repository_result = run(repository_result_command, env=environment)
            self.assertEqual(repository_result.returncode, 68)
            self.assertIn(
                "Result directory must be outside the repository",
                repository_result.stderr,
            )

            inside_run_environment = environment.copy()
            inside_run_environment["CE_RUN_HOME"] = str(repository / "run-index")
            inside_run = run(command, env=inside_run_environment)
            self.assertEqual(inside_run.returncode, 64)
            self.assertIn(
                "Run index must be outside the repository",
                inside_run.stderr,
            )
            self.assertFalse((repository / "run-index").exists())

            relative_run_environment = environment.copy()
            relative_run_environment["CE_RUN_HOME"] = "relative-run-index"
            relative_run = run(
                command,
                cwd=submodule_source,
                env=relative_run_environment,
            )
            self.assertEqual(relative_run.returncode, 64)
            self.assertIn(
                "CE_RUN_HOME (or CODEX_HOME) must resolve to an absolute path",
                relative_run.stderr,
            )

            first = run(command, env=environment)
            self.assertEqual(first.returncode, 0, first.stderr)
            manifest_path = Path(
                next(
                    line.split("=", 1)[1]
                    for line in first.stdout.splitlines()
                    if line.startswith("manifest=")
                )
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["objective_id"], "OBJ-1")
            self.assertEqual(manifest["phase_id"], "P1")
            self.assertEqual(manifest["workstream_id"], "WS-evidence")
            self.assertEqual(len(manifest["input_fingerprint"]), 64)
            self.assertEqual(len(manifest["final_diff_sha256"]), 64)

            repeated = run(command, env=environment)
            self.assertEqual(repeated.returncode, 74)
            self.assertIn("Refusing unchanged successful repeat", repeated.stderr)

            blank_repeat = run(
                [*command, "--repeat-reason", "   "],
                env=environment,
            )
            self.assertEqual(blank_repeat.returncode, 64)
            self.assertIn(
                "--repeat-reason must contain a non-whitespace justification",
                blank_repeat.stderr,
            )
            unicode_blank_repeat = run(
                [*command, "--repeat-reason", "\u00a0"],
                env=environment,
            )
            self.assertEqual(unicode_blank_repeat.returncode, 64)
            self.assertIn(
                "--repeat-reason must contain a non-whitespace justification",
                unicode_blank_repeat.stderr,
            )

            scratch.write_text("untracked v2\n", encoding="utf-8")
            changed_evidence = run(command, env=environment)
            self.assertEqual(changed_evidence.returncode, 0, changed_evidence.stderr)

            repeated_again = run(command, env=environment)
            self.assertEqual(repeated_again.returncode, 74)

            justified = run(
                [*command, "--repeat-reason", "new runtime evidence"], env=environment
            )
            self.assertEqual(justified.returncode, 0, justified.stderr)

            first_commit_environment = environment.copy()
            first_commit_environment["FAKE_CODEX_COMMIT_CONTENT"] = "commit v1"
            first_commit = run(
                [*command, "--repeat-reason", "commit fixture"],
                env=first_commit_environment,
            )
            self.assertEqual(first_commit.returncode, 0, first_commit.stderr)
            first_commit_manifest = Path(
                next(
                    line.split("=", 1)[1]
                    for line in first_commit.stdout.splitlines()
                    if line.startswith("manifest=")
                )
            )
            first_commit_diff = json.loads(
                first_commit_manifest.read_text(encoding="utf-8")
            )["final_diff_sha256"]

            second_commit_environment = environment.copy()
            second_commit_environment["FAKE_CODEX_COMMIT_CONTENT"] = "commit v2"
            second_commit = run(command, env=second_commit_environment)
            self.assertEqual(second_commit.returncode, 0, second_commit.stderr)
            second_commit_manifest = Path(
                next(
                    line.split("=", 1)[1]
                    for line in second_commit.stdout.splitlines()
                    if line.startswith("manifest=")
                )
            )
            second_commit_diff = json.loads(
                second_commit_manifest.read_text(encoding="utf-8")
            )["final_diff_sha256"]
            self.assertNotEqual(first_commit_diff, second_commit_diff)

            submodule_file = repository / "modules/evidence/evidence.txt"
            submodule_file.write_text("dirty v1\n", encoding="utf-8")
            first_dirty_submodule = run(command, env=environment)
            self.assertEqual(
                first_dirty_submodule.returncode, 0, first_dirty_submodule.stderr
            )
            repeated_dirty_submodule = run(command, env=environment)
            self.assertEqual(repeated_dirty_submodule.returncode, 74)
            submodule_file.write_text("dirty v2\n", encoding="utf-8")
            changed_dirty_submodule = run(command, env=environment)
            self.assertEqual(
                changed_dirty_submodule.returncode, 0, changed_dirty_submodule.stderr
            )
            submodule_file.write_text("clean\n", encoding="utf-8")

            submodule_untracked = repository / "modules/evidence/untracked.txt"
            submodule_untracked.write_text("a" * 32, encoding="utf-8")
            untracked_submodule = run(command, env=environment)
            self.assertEqual(
                untracked_submodule.returncode, 0, untracked_submodule.stderr
            )
            repeated_untracked_submodule = run(command, env=environment)
            self.assertEqual(repeated_untracked_submodule.returncode, 74)

            oversized_submodule_environment = environment.copy()
            oversized_submodule_environment["CE_MAX_UNTRACKED_FINGERPRINT_BYTES"] = "16"
            oversized_submodule = run(
                command,
                env=oversized_submodule_environment,
            )
            self.assertNotEqual(oversized_submodule.returncode, 0)
            self.assertIn(
                "Refusing to fingerprint oversized untracked file",
                oversized_submodule.stderr,
            )
            submodule_untracked.unlink()

            scratch.unlink()
            outside_link.unlink()
            fingerprint_failure_environment = environment.copy()
            fingerprint_failure_environment.update(
                {
                    "CE_MAX_UNTRACKED_FINGERPRINT_BYTES": "4",
                    "FAKE_CODEX_UNTRACKED_FILE": "generated.bin",
                }
            )
            fingerprint_failure = run(command, env=fingerprint_failure_environment)
            self.assertEqual(fingerprint_failure.returncode, 75)
            failed_manifest_path = Path(
                next(
                    line.split("=", 1)[1]
                    for line in fingerprint_failure.stdout.splitlines()
                    if line.startswith("manifest=")
                )
            )
            failed_manifest = json.loads(
                failed_manifest_path.read_text(encoding="utf-8")
            )
            self.assertEqual(failed_manifest["codex_exit_status"], 0)
            self.assertEqual(
                failed_manifest["fingerprint_state"],
                "post_run_fingerprint_failed",
            )
            self.assertEqual(failed_manifest["exit_status"], 75)


if __name__ == "__main__":
    unittest.main()
