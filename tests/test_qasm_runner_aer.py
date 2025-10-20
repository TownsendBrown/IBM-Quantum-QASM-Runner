import os
import json
import subprocess
import pytest

def test_simple_qasm_execution(tmp_path):
    """
    Verify that qasm_runner_aer.py executes a QASM file correctly and
    produces a reasonable distribution for a Bell state.
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

    # Ensure command executed successfully
    assert result.returncode == 0, f"Runner failed: {result.stderr}"

    # Find JSON output file
    saved_json_files = [f for f in os.listdir() if f.endswith(".json")]
    assert saved_json_files, "No JSON results file found"

    # Load the last created JSON file
    with open(saved_json_files[-1], "r") as f:
        data = json.load(f)

    # Validate structure
    assert "results" in data, "Missing 'results' key in output"
    assert len(data["results"]) == 1, "Expected one circuit result"

    result_entry = data["results"][0]
    counts = result_entry.get("results", [])
    assert counts, "No measurement results found"

    # Aggregate total counts and check Bell state probabilities
    prob_00 = next((r["probability"] for r in counts if r["outcome"] == "00"), 0)
    prob_11 = next((r["probability"] for r in counts if r["outcome"] == "11"), 0)

    # Should be ~0.5 each (within 0.15 margin)
    assert abs(prob_00 - 0.5) < 0.15, f"Unexpected P(00): {prob_00}"
    assert abs(prob_11 - 0.5) < 0.15, f"Unexpected P(11): {prob_11}"

    print("✅ Aer QASM Runner test passed successfully.")
