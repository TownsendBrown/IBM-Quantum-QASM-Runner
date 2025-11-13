# Qiskit QASM Runner for IBM Hardware and Simulators
"[![Qiskit Ecosystem](https://img.shields.io/endpoint?style=flat&url=https%3A%2F%2Fqiskit.github.io%2Fecosystem%2Fb%2F5b05d5a3)](https://qisk.it/e)"
Vibe coded Python CLI tool to execute .qasm files on the IBM Quantum Platform.
## Why?

This program was made to help make quantum computing more accessible by giving users the ability to simply take files written in OpenQASM and run them on IBM hardware and locally run simulators.

## Features

- Execute .qasm files on IBM Quantum backends
- Support for multiple .qasm files in a single run
- Configurable number of shots
- Backend selection (automatic or manual)
- Built-in API connection testing
- Backend listing functionality
- Comprehensive error handling and user feedback

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Configure your IBM Quantum API key using one of these methods:

   **Option A: Using config.json (recommended for local development)**
   ```json
   {
     "ibm_api_key": "your_ibm_quantum_api_key_here",
     "qubit_limit": 100
   }
   ```

   **Option B: Using environment variables (recommended for CI/CD)**
   ```bash
   export QISKIT_IBM_TOKEN="your_ibm_quantum_api_key_here"
   # OR
   export IBM_API_KEY="your_ibm_quantum_api_key_here"
   ```

Get your API key from: https://quantum-computing.ibm.com/

## Usage

### Interactive Mode (Default Behavior)

The application runs in interactive mode by default, whether you provide .qasm files or not:

```bash
# Interactive mode with file specified
python3 qasm_runner.py circuit.qasm

# Interactive mode without files (will prompt for files)
python3 qasm_runner.py
```

The interactive mode will prompt you for:
1. **QASM file path(s)** - Only if no files were provided on command line
2. **Number of shots** - Choose between 0-10,000 shots (default: 1024)
3. **Backend selection** - Browse and select from available IBM Quantum backends
4. **Response format** - Choose between human-readable or JSON output
5. **Visualization** - Option to generate circuit diagram
6. **JSON file saving** - Option to save results to JSON file

### Command Line Usage

```bash
# Run a single .qasm file with default settings
python3 qasm_runner.py circuit.qasm

# Run multiple .qasm files
python3 qasm_runner.py circuit1.qasm circuit2.qasm circuit3.qasm

# Run with custom number of shots
python3 qasm_runner.py circuit.qasm --shots 2048

# Use a specific backend
python3 qasm_runner.py circuit.qasm --backend ibm_brisbane

# Output results in JSON format
python3 qasm_runner.py circuit.qasm --json

# Interactively select backend
python3 qasm_runner.py circuit.qasm --interactive
```

### Testing and Information

```bash
# Test IBM Quantum API connection
python3 qasm_runner.py --test

# List all available backends
python3 qasm_runner.py --list-backends
```

### Non-Interactive Mode (CI/CD)

The application automatically detects non-interactive environments (e.g., CI/CD pipelines) and skips interactive prompts. In non-interactive mode, it will:
- Use the first available backend if none is specified
- Use default values for any unspecified options
- Exit with an error if required files are not provided

```bash
# Non-interactive mode (automatically detected in CI/CD)
python3 qasm_runner.py circuit.qasm --shots 256 --json --save-json
```

You can also explicitly enable non-interactive mode:
```bash
python3 qasm_runner.py circuit.qasm --non-interactive
```

### Command Line Options

- `qasm_files`: One or more .qasm files to execute (optional - will prompt for files if omitted)
- `--shots N`: Number of shots to run (default: 1024) - overrides interactive prompt
- `--backend NAME`: Specific backend to use - overrides interactive prompt
- `--interactive`: Interactively select backend (legacy flag, now default behavior)
- `--non-interactive`: Run in non-interactive mode (auto-select first available backend)
- `--json`: Output results in JSON format - overrides interactive prompt
- `--visualize`: Generate circuit diagram visualization (saved as PNG)
- `--save-json`: Save results to JSON file (filename based on .qasm file)
- `--test`: Run IBM Quantum API connection test
- `--list-backends`: List all available backends
- `--help`: Show help message

**Note**: The application now runs in interactive mode by default. Command-line flags will override the interactive prompts when specified. In non-interactive environments (e.g., CI/CD), interactive prompts are automatically skipped.

### Visualization and Output Options

#### Circuit Diagram
When `--visualize` is enabled, a circuit diagram is generated using Qiskit's built-in visualization:
- **Filename**: `<qasm_filename>_circuit_diagram.png`
- **Location**: Current directory
- **Format**: PNG image (300 DPI)

#### JSON File Output
When `--save-json` is enabled, results are saved to a JSON file:
- **Filename**: `<qasm_filename>_results_<timestamp>.json`
- **Location**: Current directory
- **Contents**: Same data as console JSON output, includes visualization paths if enabled

**Example with all options:**
```bash
python3 qasm_runner.py circuit.qasm --shots 100 --backend ibm_brisbane --visualize --save-json --json
```

## Example .qasm File

The repository includes a sample Bell state circuit (`sample_circuit.qasm`):

```qasm
OPENQASM 2.0;
include "qelib1.inc";

qreg q[2];
creg c[2];

// Create a Bell state
h q[0];
cx q[0],q[1];

// Measure both qubits
measure q[0] -> c[0];
measure q[1] -> c[1];
```

## Error Handling

The tool provides comprehensive error handling for:
- Missing or invalid .qasm files
- Network connectivity issues
- Authentication problems
- Backend unavailability
- Job execution failures

## Dependencies

- `qiskit>=0.45.0`: Quantum computing framework
- `qiskit-ibm-runtime>=0.15.0`: IBM Quantum Runtime integration
- `qiskit-aer>=0.13.0`: Quantum circuit simulator

## JSON Output

When using the `--json` flag, the application returns structured JSON output with:

- **Summary**: Total files processed, success/failure counts, timestamp
- **Results**: For each file:
  - `success`: Boolean indicating if execution succeeded
  - `results`: Array of measurement outcomes with probabilities and counts
  - `metadata`: Job details, backend info, circuit info, execution timing
  - `file`: Path to the processed file

Example JSON output:
```json
{
  "summary": {
    "total_files": 1,
    "successful_files": 1,
    "failed_files": 0,
    "timestamp": "2025-09-30T11:53:28.782758"
  },
  "results": [
    {
      "success": true,
      "results": [
        {
          "outcome": "00",
          "probability": 0.5,
          "percentage": 50.0,
          "count": 5
        }
      ],
      "metadata": {
        "job_id": "d3e2e6c86mts73cdfnl0",
        "backend": {
          "name": "ibm_brisbane",
          "qubits": 127,
          "operational": true,
          "simulator": false
        },
        "circuit": {
          "original_qubits": 2,
          "transpiled_qubits": 127,
          "transpiled_depth": 10
        },
        "execution": {
          "shots": 10,
          "duration_seconds": 16.89
        }
      },
      "file": "sample_circuit.qasm"
    }
  ]
}
```

## Testing

### Manual Testing

Run the built-in test to verify your setup:

```bash
python qasm_runner.py --test
```

This will test your API key, list available backends, and optionally run a simple quantum circuit.

### Automated Testing (pytest)

The repository includes automated tests:

```bash
# Install test dependencies
pip install -r requirements.txt pytest

# Run simulator tests (no API key required)
pytest tests/test_qasm_runner_aer.py -v

# Run IBM runtime tests (requires IBM_API_KEY environment variable)
export IBM_API_KEY="your_api_key_here"
pytest tests/test_qasm_runner_ibm.py -v

# Run all tests
pytest tests/ -v
```

### CI/CD Integration

The repository includes a GitHub Actions workflow (`.github/workflows/test.yml`) that:
- ✅ Always runs simulator tests (using `qiskit-aer`)
- 🔐 Only runs IBM runtime tests if `IBM_API_KEY` is configured in repository secrets
- ⏭️ Skips IBM tests gracefully if no API key is available

To enable IBM runtime tests in your fork:
1. Go to your repository's Settings → Secrets and variables → Actions
2. Add a new repository secret named `IBM_API_KEY`
3. Set the value to your IBM Quantum API key

The workflow will automatically detect the secret and run IBM tests on all pushes and pull requests.

## Qiskit Ecosystem Integration

This project is part of the Qiskit Ecosystem and extends Qiskit's functionality by providing a
command-line automation layer for executing OpenQASM 2.0 circuits directly on IBM Quantum
backends via the `qiskit-ibm-runtime` API or locally using `qiskit-aer`.

### Core Qiskit Dependencies
- **qiskit** – for circuit parsing, transpilation, and visualization  
- **qiskit-ibm-runtime** – for connecting to IBM Quantum systems and executing real hardware jobs  
- **qiskit-aer** – for high-performance local simulation  

### Integration Overview
The QASM Runner CLI bridges the gap between OpenQASM files and Qiskit-based execution environments,
enabling users to:
- Run `.qasm` circuits on both **cloud** (IBM Quantum) and **local** (Aer) backends  
- Automatically visualize circuits and save structured JSON outputs  
- Verify IBM Quantum API connectivity and list available backends  
- Support reproducible, scriptable workflows using standard Qiskit primitives  

This tool complements Qiskit’s mission to make quantum computing accessible by providing a
lightweight, user-friendly CLI that can be run interactively or in automated pipelines.
