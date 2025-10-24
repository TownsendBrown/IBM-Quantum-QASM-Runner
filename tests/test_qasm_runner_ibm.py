import os
import json
import subprocess
import pytest

@pytest.mark.skipif(
    not os.environ.get("IBM_API_KEY", "").strip(),
    reason="IBM Quantum API key not found; skipping cloud test."
)
def test_ibm_runtime_execution(tmp_path):
    """
    Integration test for qasm_runner.py.
    Executes a QASM file on IBM Quantum backend (using the runtime API).
    Skips automatically if IBM_API_KEY environment variable is not set or empty.
    """

    qasm_file = "simple_test.qasm"
    assert os.path.exists(qasm_file), f"Missing QASM file: {qasm_file}"

    env = os.environ.copy()
    env["QISKIT_IBM_TOKEN"] = env.get("IBM_API_KEY")

    result = subprocess.run(
        [
            "python3",
            "qasm_runner.py",
            qasm_file,
            "--shots", "256",
            "--json",
            "--save-json"
        ],
        capture_output=True,
        text=True,
        env=env,
        timeout=600
    )

    assert result.returncode == 0, f"Runner failed: {result.stderr}"

    # Find JSON result file
    saved_json_files = [f for f in os.listdir() if f.endswith(".json")]
    assert saved_json_files, "No JSON output file found"

    with open(saved_json_files[-1], "r") as f:
        data = json.load(f)

    assert "results" in data, "Missing 'results' in JSON output"
    assert isinstance(data["results"], list), "Results not a list"

    result_entry = data["results"][0]
    metadata = result_entry.get("metadata", {})
    backend = metadata.get("backend", {})

    assert backend, "No backend metadata found"
    assert "name" in backend, "Backend name missing"
    assert "operational" in backend, "Backend operational flag missing"

    print(f"✅ IBM Quantum Runtime test passed on backend: {backend['name']}")
