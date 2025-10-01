# IBM Quantum QASM Runner

A command-line tool for executing OpenQASM 2.0 files on IBM Quantum hardware and simulators.

## 📋 Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Command Reference](#command-reference)
- [Output Formats](#output-formats)
- [Examples](#examples)
- [Error Handling](#error-handling)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](LICENSE)

## ✨ Features

| Feature | Description |
|---------|-------------|
| **QASM Execution** | Execute OpenQASM 2.0 files on real quantum hardware or simulators |
| **Interactive Mode** | Guided setup for backend selection and execution parameters |
| **Batch Processing** | Process multiple QASM files in a single run |
| **Circuit Visualization** | Generate circuit diagrams from QASM files |
| **Result Persistence** | Save execution results to timestamped JSON files |
| **Backend Management** | List and select from available IBM Quantum backends |
| **Qubit Validation** | Automatic validation against configurable qubit limits |
| **Multiple Output Formats** | Human-readable or JSON formatted output |

## 📦 Requirements

### System Requirements
| Component | Version |
|-----------|---------|
| Python | ≥ 3.8 |
| Operating System | Windows, macOS, Linux |

### Python Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| qiskit | ≥ 0.45.0 | Quantum circuit manipulation |
| qiskit-ibm-runtime | ≥ 0.15.0 | IBM Quantum backend access |
| matplotlib | ≥ 3.5.0 | Circuit visualization |

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/ibm-quantum-qasm-runner.git
cd ibm-quantum-qasm-runner
```

### 2. Install Dependencies
```bash
pip install qiskit qiskit-ibm-runtime matplotlib
```

### 3. Configure IBM Quantum Access
Create a `config.json` file in the project directory:

```json
{
    "ibm_api_key": "YOUR_IBM_QUANTUM_API_KEY",
    "qubit_limit": 100
}
```

To obtain an API key:
1. Visit [IBM Quantum Platform](https://quantum-computing.ibm.com/)
2. Create an account or sign in
3. Navigate to Account Settings → API Token

## 🔧 Configuration

### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ibm_api_key` | string | Required | IBM Quantum Platform API key |
| `qubit_limit` | integer | 100 | Maximum qubits allowed per circuit |

## 📖 Usage

### Interactive Mode
Launch without arguments for guided setup:
```bash
python qasm_runner.py
```

### Direct Execution
Execute a QASM file with default settings:
```bash
python qasm_runner.py circuit.qasm
```

### Advanced Usage
```bash
python qasm_runner.py circuit.qasm --shots 2048 --backend ibm_torino --visualize --save-json
```

## 🛠️ Command Reference

### Main Commands

| Command | Description |
|---------|-------------|
| `python qasm_runner.py [files]` | Execute QASM file(s) |
| `python qasm_runner.py --test` | Test IBM Quantum API connection |
| `python qasm_runner.py --list-backends` | List available backends |

### Command-Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `qasm_files` | string(s) | - | Path(s) to .qasm files |
| `--shots` | integer | 1024 | Number of measurement shots |
| `--backend` | string | Auto | Specific backend name |
| `--interactive` | flag | False | Interactive backend selection |
| `--json` | flag | False | Output in JSON format |
| `--visualize` | flag | False | Generate circuit diagrams |
| `--save-json` | flag | False | Save results to JSON file |
| `--test` | flag | False | Run API connection test |
| `--list-backends` | flag | False | List all backends |

## 📊 Output Formats

### Human-Readable Output
```
🚀 Processing file 1/1: grover.qasm
----------------------------------------
✓ Circuit created: 2 qubits, 2 classical bits
✓ Qubit check passed: 2 qubits (limit: 100)
🔐 Authenticating with IBM Quantum...
✓ Using backend: ibm_torino
📊 Results:
   Measurement outcomes:
     |10⟩: 474 counts (0.9480 = 94.80%)
     |00⟩: 12 counts (0.0240 = 2.40%)
     |11⟩: 11 counts (0.0220 = 2.20%)
     |01⟩: 3 counts (0.0060 = 0.60%)
```

### JSON Output Structure
```json
{
  "summary": {
    "total_files": 1,
    "successful_files": 1,
    "failed_files": 0,
    "timestamp": "2025-09-30T18:47:34.915872"
  },
  "results": [{
    "success": true,
    "file": "grover.qasm",
    "results": [
      {
        "outcome": "10",
        "probability": 0.948,
        "percentage": 94.8,
        "count": 474
      }
    ],
    "metadata": {
      "job_id": "d3e8g9s1nk1s739lcnkg",
      "backend": {
        "name": "ibm_torino",
        "qubits": 133,
        "operational": true,
        "pending_jobs": 644,
        "simulator": false
      },
      "circuit": {
        "original_qubits": 2,
        "transpiled_qubits": 133,
        "transpiled_depth": 10
      },
      "execution": {
        "shots": 500,
        "duration_seconds": 15.76
      }
    }
  }]
}
```

## 📚 Examples

### Example 1: Basic Grover's Algorithm
```bash
# Execute with default settings
python qasm_runner.py grover.qasm

# Execute with custom shots
python qasm_runner.py grover.qasm --shots 2048

# Execute with visualization
python qasm_runner.py grover.qasm --visualize
```

### Example 2: Batch Processing
```bash
# Process multiple QASM files
python qasm_runner.py circuit1.qasm circuit2.qasm circuit3.qasm

# Process with JSON output and save
python qasm_runner.py *.qasm --json --save-json
```

### Example 3: Backend Selection
```bash
# List available backends
python qasm_runner.py --list-backends

# Use specific backend
python qasm_runner.py circuit.qasm --backend ibm_brisbane

# Interactive backend selection
python qasm_runner.py circuit.qasm --interactive
```

## ⚠️ Error Handling

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `config.json file not found` | Missing configuration | Create config.json with API key |
| `Qubit limit exceeded` | Circuit too large | Increase `qubit_limit` in config.json |
| `Backend not found` | Invalid backend name | Use `--list-backends` to see available options |
| `Job timeout` | Long queue or execution | Retry or use different backend |
| `No operational backends` | All backends offline | Wait and retry later |

## 🔌 API Reference

### Core Functions

| Function | Parameters | Returns | Description |
|----------|-----------|---------|-------------|
| `load_config()` | None | Dict | Load configuration from config.json |
| `validate_qasm_file(file_path)` | str | bool | Validate QASM file existence and extension |
| `count_qubits_in_qasm(content)` | str | int | Parse QASM to count qubits |
| `create_circuit_from_qasm(content)` | str | QuantumCircuit | Create Qiskit circuit from QASM |
| `execute_circuit_on_ibm(...)` | Multiple | Dict | Execute circuit on IBM Quantum |
| `generate_circuit_diagram(circuit, path)` | QuantumCircuit, str | str | Generate and save circuit visualization |
| `save_json_results(data, path)` | Dict, str | str | Save results to JSON file |

### Result Dictionary Structure

| Key | Type | Description |
|-----|------|-------------|
| `success` | bool | Execution success status |
| `file` | str | Source QASM file path |
| `results` | List[Dict] | Measurement outcomes with probabilities |
| `metadata` | Dict | Execution metadata (backend, timing, etc.) |
| `error` | str | Error message (if failed) |
| `visualization` | Dict | Paths to generated visualizations |

## 📈 Performance Considerations

### Optimization Tips

| Aspect | Recommendation |
|--------|----------------|
| **Shot Count** | Use 1024-4096 for statistical significance |
| **Backend Selection** | Prefer simulators for testing, hardware for final results |
| **Batch Size** | Process 5-10 circuits per batch to avoid timeouts |
| **Qubit Count** | Keep under 10 qubits for real hardware |

## 🤝 Contributing

Contributions are welcome! Please ensure:
- Code follows existing style patterns
- Functions include docstrings
- Error handling is comprehensive
- New features include documentation

## 🔗 Links

- [IBM Quantum Platform](https://quantum-computing.ibm.com/)
- [OpenQASM Documentation](https://github.com/openqasm/openqasm)
- [Qiskit Documentation](https://qiskit.org/documentation/)

## 💡 Support

For issues or questions:
1. Check the error handling section
2. Verify your IBM Quantum API key is valid
3. Ensure all dependencies are installed
4. Run `python qasm_runner.py --test` to verify connectivity
