from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT = REPO_ROOT / "skill/chief-engineer/scripts/ce-token-report.py"
DISPATCH = REPO_ROOT / "skill/chief-engineer/scripts/ce-dispatch.sh"


def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=False,
        text=True,
        capture_output=True,
        **kwargs,
    )


class TokenReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.codex_home = Path(self.tempdir.name)
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
        self, objective_id: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        command = [
            "python3",
            str(REPORT),
            "--date",
            "2026-07-24",
            "--codex-home",
            str(self.codex_home),
        ]
        if objective_id:
            command.extend(["--objective-id", objective_id])
        return run(command)

    def write_manifest(
        self,
        run_id: str,
        *,
        fingerprint: str,
        started: int,
        finished: int,
        repeat_reason: str = "",
        role: str = "worker",
    ) -> Path:
        directory = self.codex_home / "chief-engineer-runs/2026-07-24"
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
            "exit_status": 0,
            "input_fingerprint": hashlib.sha256(fingerprint.encode()).hexdigest(),
            "repeat_reason": repeat_reason,
            "started_at_epoch": started,
            "finished_at_epoch": finished,
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

            scratch.write_text("untracked v2\n", encoding="utf-8")
            changed_evidence = run(command, env=environment)
            self.assertEqual(changed_evidence.returncode, 0, changed_evidence.stderr)

            repeated_again = run(command, env=environment)
            self.assertEqual(repeated_again.returncode, 74)

            justified = run(
                [*command, "--repeat-reason", "new runtime evidence"], env=environment
            )
            self.assertEqual(justified.returncode, 0, justified.stderr)

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
