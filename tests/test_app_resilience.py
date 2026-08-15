from pathlib import Path


def test_app_guards_evidence_loading_and_benchmark_timeout():
    source = Path("app.py").read_text(encoding="utf-8")
    assert "except RuntimeError as exc" in source
    assert "except subprocess.TimeoutExpired" in source
    assert "st.stop()" in source


def test_run_demo_shell_script_has_valid_posix_syntax():
    script = Path("run_demo.sh")
    assert script.exists()
    source = script.read_text(encoding="utf-8")
    assert source.startswith("#!/usr/bin/env sh\n")
    assert "set -eu" in source
    assert "pnpm install --frozen-lockfile" in source
    assert "exec pnpm dev" in source
