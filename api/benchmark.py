from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from http.server import BaseHTTPRequestHandler
from pathlib import Path

# Vercel traces imports from the function entry point when optimizing large
# Python bundles. The benchmark runs in a child process, so its scientific
# dependencies must also be visible here or the optimizer can omit them.
import numpy
import pandas
import scipy
import sklearn
import yaml


ROOT = Path(__file__).resolve().parents[1]
TIMEOUT_SECONDS = 210
_RUNTIME_IMPORT_GUARD = (numpy, pandas, scipy, sklearn, yaml)


class handler(BaseHTTPRequestHandler):
    @staticmethod
    def _ready_payload() -> dict:
        return {
            "status": "ready",
            "mode": "illustrative_quick_run",
            "evidence_boundary": "Quick-run output is not submission-grade five-seed evidence.",
        }

    def _respond(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_HEAD(self) -> None:
        body = json.dumps(self._ready_payload()).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()

    def do_GET(self) -> None:
        self._respond(200, self._ready_payload())

    def do_POST(self) -> None:
        run_root = Path(tempfile.mkdtemp(prefix="aegisloop-quick-"))
        output = run_root / "artifacts"
        command = [
            sys.executable,
            str(ROOT / "experiments" / "run_benchmark.py"),
            "--quick",
            "--output",
            str(output),
        ]
        child_environment = os.environ.copy()
        child_environment["PYTHONPATH"] = os.pathsep.join(str(entry) for entry in sys.path)
        try:
            completed = subprocess.run(
                command,
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
                check=False,
                env=child_environment,
            )
            if completed.returncode != 0:
                self._respond(
                    500,
                    {
                        "status": "failed",
                        "message": "The illustrative benchmark exited without completing.",
                        "diagnostic": (completed.stderr or completed.stdout)[-4000:],
                    },
                )
                return
            artifact_files = sorted(path.name for path in output.glob("*"))
            summary_path = output / "summary.json"
            summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else None
            self._respond(
                200,
                {
                    "status": "complete",
                    "protocol": "illustrative_quick_run",
                    "evidence_boundary": (
                        "Generated live from the smaller quick protocol. Do not compare these values "
                        "with the archived full five-seed evidence."
                    ),
                    "artifact_files": artifact_files,
                    "summary": summary,
                    "stdout": completed.stdout,
                },
            )
        except subprocess.TimeoutExpired:
            self._respond(
                504,
                {
                    "status": "timed_out",
                    "message": "The illustrative benchmark exceeded its server-side execution limit.",
                },
            )
        except OSError as error:
            self._respond(
                503,
                {
                    "status": "unavailable",
                    "message": "The benchmark process could not be started.",
                    "diagnostic": str(error),
                },
            )
        finally:
            shutil.rmtree(run_root, ignore_errors=True)
