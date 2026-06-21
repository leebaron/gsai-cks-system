#!/usr/bin/env python3
"""
CI Truth Extraction Tool v1.0
Extracts execution graph from repo runtime evidence.

Output: execution_graph.json with 3 layers:
  Layer 1: Static (code presence)
  Layer 2: Import (code connectivity)
  Layer 3: Execution (runtime evidence — only truth)

Usage:
    python3 tools/extract_runtime.py > execution_graph.json
"""
import sys, json, subprocess, hashlib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def hash_output(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def run_cmd(cmd: list, cwd: str = None) -> dict:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd or str(REPO_ROOT),
            timeout=30,
        )
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "log_hash": hash_output(result.stdout + result.stderr),
        }
    except subprocess.TimeoutExpired:
        return {"exit_code": -1, "stdout": "", "stderr": "TIMEOUT", "log_hash": "TIMEOUT"}
    except FileNotFoundError:
        return {"exit_code": -2, "stdout": "", "stderr": "CMD_NOT_FOUND", "log_hash": "N/A"}


def extract_execution_graph() -> dict:
    graph = {}

    # Layer 1: Static — file existence
    py_files = sorted(REPO_ROOT.rglob("*.py"))
    static = {
        "total_py_files": len(py_files),
        "files": [str(f.relative_to(REPO_ROOT)) for f in py_files],
    }
    graph["static"] = static

    # Layer 2: Import — connectivity
    imports = {}
    for f in py_files:
        rel = str(f.relative_to(REPO_ROOT))
        try:
            with open(f) as fh:
                lines = fh.readlines()
        except:
            lines = []
        imported = []
        for line in lines:
            line = line.strip()
            if line.startswith("from ") or line.startswith("import "):
                imported.append(line)
        if imported:
            imports[rel] = imported
    graph["imports"] = {"modules_with_imports": len(imports), "edges": imports}

    # Layer 3: Execution — runtime evidence (only truth)
    execution = {}

    # 3a. pytest
    execution["pytest"] = run_cmd(["python3", "-m", "pytest", "-q", "tests/"])

    # 3b. ROEL gate
    roel_test = subprocess.run(
        ["python3", "roel.py"],
        input="VIEW_STATE: COMPLETE\nROEL CI truth gate test.\n",
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=10,
    )
    execution["roel_gate"] = {
        "exit_code": roel_test.returncode,
        "stdout": roel_test.stdout,
        "stderr": roel_test.stderr,
        "log_hash": hash_output(roel_test.stdout + roel_test.stderr),
        "gate_passed": roel_test.returncode == 0,
    }

    # 3c. ROEL table rejection
    roel_reject = subprocess.run(
        ["python3", "roel.py"],
        input="VIEW_STATE: COMPLETE\n| col | val |\n| a | b |\n",
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=10,
    )
    execution["roel_table_reject"] = {
        "exit_code": roel_reject.returncode,
        "stderr": roel_reject.stderr.strip(),
        "log_hash": hash_output(roel_reject.stdout + roel_reject.stderr),
        "table_blocked": roel_reject.returncode == 1,
    }

    # 3d. Ledger hash chain validation
    chain_test = subprocess.run(
        ["python3", "ledger/validate_chain.py"],
        input=json.dumps([
            {"index": 0, "hash": "a000", "prev_hash": "GENESIS"},
            {"index": 1, "hash": "b111", "prev_hash": "a000"},
        ]),
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=10,
    )
    chain_result = json.loads(chain_test.stdout) if chain_test.stdout else {}
    execution["hash_chain"] = {
        "exit_code": chain_test.returncode,
        "chain_valid": chain_result.get("valid", False),
        "log_hash": hash_output(chain_test.stdout + chain_test.stderr),
    }

    graph["execution"] = execution

    # Git commit
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True,
            cwd=str(REPO_ROOT), timeout=5,
        ).stdout.strip()
    except:
        commit = "unknown"
    graph["commit"] = commit

    return graph


def main():
    graph = extract_execution_graph()
    output = json.dumps(graph, indent=2)

    # Write to file
    out_path = REPO_ROOT / "execution_graph.json"
    out_path.write_text(output)

    sys.stdout.write(output)
    sys.exit(0)


if __name__ == "__main__":
    main()
