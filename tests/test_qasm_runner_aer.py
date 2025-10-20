import os
import json
import subprocess
import pytest

def test_simple_qasm_execution(tmp_path):
    """
    Verify that qasm_runner_aer.py executes a QASM file correctly and
    produces a reasonable distribution for a Bell or 1-qubit test circuit.
    """

    qasm_file = "simple_test.qasm"
    assert os.path.exists(qasm_file), f"Missing test file: {qasm_file}"

    # Run the QASM file using the Aer runner with JSON output
    result = subprocess.run(
        [
            "python3",
            "qasm_runner_aer.py",
            qasm_file,
            "--shots", "512",
            "--json",
            "--save-json"
        ],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, f"Runner failed: {result.stderr}"

    # Find JSON output file
    saved_json_files = [f for f in os.listdir() if f.endswith(".json")]
    assert saved_json_files, "No JSON results file found"

    # Load last JSON file
    with open(saved_json_files[-1], "r") as f:
        data = json.load(f)

    # Normalize data structure: handle both 'results' and 'result' top-level keys
    if "results" in data:
        result_entry = data["results"][0]
    elif "result" in data:
        result_entry = data["result"]
    else:
        raise AssertionError(f"Unexpected JSON structure: {list(data.keys())}")

    # Extract measurement results
    counts = result_entry.get("results", [])
    assert counts, "No measurement results found"

    # Extract probabilities
    probs = {r["outcome"]: r["probability"] for r in counts}
    total_prob = sum(probs.values())
    assert abs(total_prob - 1.0) < 0.2, "Probabilities do not sum close to 1"

    # Basic validation of measurement outcomes
    assert any(k in probs for k in ("0", "1", "00", "11")), "Unexpected measurement keys"

    print("✅ Aer QASM Runner JSON format and probabilities validated successfully.")
