#!/usr/bin/env python3
"""
IBM Quantum QASM Runner CLI
A command-line tool to execute .qasm files on IBM Quantum Platform.
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

def load_config() -> Dict[str, Any]:
    """Load configuration from config.json file or use environment variables."""
    config_path = Path(__file__).parent / "config.json"
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Check if API key is available via environment variables
        if os.environ.get('QISKIT_IBM_TOKEN') or os.environ.get('IBM_API_KEY'):
            # Return a minimal config with default values
            return {
                'ibm_api_key': None,  # Will be loaded from env vars later
                'qubit_limit': 100
            }
        print("❌ config.json file not found and no API key in environment variables")
        print("💡 Please ensure config.json exists with your IBM Quantum API key")
        print("💡 Or set QISKIT_IBM_TOKEN or IBM_API_KEY environment variable")
        sys.exit(1)
    except json.JSONDecodeError:
        print("❌ Invalid JSON in config.json")
        sys.exit(1)

def validate_qasm_file(file_path: str) -> bool:
    """Validate that the file exists and has .qasm extension."""
    path = Path(file_path)
    if not path.exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    if path.suffix.lower() != '.qasm':
        print(f"❌ File must have .qasm extension: {file_path}")
        return False
    
    return True

def count_qubits_in_qasm(qasm_content: str) -> int:
    """
    Comprehensive qubit counting from QASM content.
    
    Parses QASM content to count total qubits from qreg declarations.
    Handles multiple qubit registers and ignores comments.
    
    Args:
        qasm_content: The QASM file content as a string
        
    Returns:
        Total number of qubits across all qubit registers
    """
    total_qubits = 0
    
    # Remove comments to avoid false positives
    # Remove single-line comments (// ...)
    content_no_comments = re.sub(r'//.*$', '', qasm_content, flags=re.MULTILINE)
    # Remove multi-line comments (/* ... */)
    content_no_comments = re.sub(r'/\*.*?\*/', '', content_no_comments, flags=re.DOTALL)
    
    # Find all qreg declarations
    # Pattern matches: qreg name[size];
    # Examples: qreg q[5]; qreg quantum_register[10]; qreg a[3];
    qreg_pattern = r'qreg\s+(\w+)\s*\[\s*(\d+)\s*\]\s*;'
    matches = re.findall(qreg_pattern, content_no_comments, re.IGNORECASE)
    
    for register_name, size_str in matches:
        try:
            size = int(size_str)
            if size > 0:  # Only count registers with positive size
                total_qubits += size
        except ValueError:
            continue
    
    return total_qubits

def validate_qubit_count_with_qiskit(qasm_content: str, file_path: str) -> int:
    """
    Validate qubit count using Qiskit and return actual count.
    
    Args:
        qasm_content: The QASM file content
        file_path: Path to the QASM file for error reporting
        
    Returns:
        Actual qubit count from Qiskit circuit
        
    Raises:
        SystemExit: If circuit creation fails
    """
    try:
        from qiskit import QuantumCircuit
        circuit = QuantumCircuit.from_qasm_str(qasm_content)
        return circuit.num_qubits
    except Exception as e:
        print(f"❌ Error creating circuit from QASM: {e}")
        print(f"   File: {file_path}")
        sys.exit(1)

def check_qubit_limit(file_path: str, config: Dict[str, Any]) -> bool:
    """
    Check if QASM file exceeds the configured qubit limit.
    
    Args:
        file_path: Path to the QASM file
        config: Configuration dictionary containing qubit_limit
        
    Returns:
        True if qubit count is within limit, False otherwise
        
    Raises:
        SystemExit: If qubit limit is exceeded
    """
    try:
        with open(file_path, 'r') as f:
            qasm_content = f.read()
    except Exception as e:
        print(f"❌ Error reading QASM file {file_path}: {e}")
        sys.exit(1)
    
    # Get qubit limit from config
    qubit_limit = config.get('qubit_limit', 100)
    
    # Parse QASM to count qubits
    parsed_qubits = count_qubits_in_qasm(qasm_content)
    
    # Validate with Qiskit
    actual_qubits = validate_qubit_count_with_qiskit(qasm_content, file_path)
    
    # Check if counts match (sanity check)
    if parsed_qubits != actual_qubits:
        print(f"⚠️  Warning: Parsed qubit count ({parsed_qubits}) doesn't match Qiskit count ({actual_qubits})")
        print(f"   Using Qiskit count: {actual_qubits}")
    
    # Check against limit
    if actual_qubits > qubit_limit:
        print(f"❌ Qubit limit exceeded!")
        print(f"   File: {file_path}")
        print(f"   Qubit count: {actual_qubits}")
        print(f"   Configured limit: {qubit_limit}")
        print(f"   💡 Increase the 'qubit_limit' in config.json or reduce circuit size")
        sys.exit(1)
    
    print(f"✓ Qubit check passed: {actual_qubits} qubits (limit: {qubit_limit})")
    return True

def generate_circuit_diagram(circuit, file_path: str) -> str:
    """
    Generate and save circuit diagram using Qiskit visualization.
    
    Args:
        circuit: Qiskit QuantumCircuit object
        file_path: Original QASM file path for naming
        
    Returns:
        Path to the saved diagram file
    """
    try:
        from qiskit.visualization import circuit_drawer
        import matplotlib.pyplot as plt
        
        # Generate filename based on QASM file
        qasm_filename = Path(file_path).stem
        diagram_path = f"{qasm_filename}_circuit_diagram.png"
        
        # Create circuit diagram
        fig = circuit_drawer(circuit, output='mpl', style='iqx')
        fig.savefig(diagram_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        print(f"📊 Circuit diagram saved: {diagram_path}")
        return diagram_path
        
    except Exception as e:
        print(f"⚠️  Warning: Could not generate circuit diagram: {e}")
        return ""

def save_json_results(results_data: Dict[str, Any], file_path: str) -> str:
    """
    Save results to JSON file.
    
    Args:
        results_data: Complete results dictionary
        file_path: Original QASM file path for naming
        
    Returns:
        Path to the saved JSON file
    """
    try:
        # Generate filename based on QASM file
        qasm_filename = Path(file_path).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = f"{qasm_filename}_results_{timestamp}.json"
        
        # Save to JSON file
        with open(json_path, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"💾 Results saved to JSON: {json_path}")
        return json_path
        
    except Exception as e:
        print(f"⚠️  Warning: Could not save JSON file: {e}")
        return ""

def parse_qasm_file(file_path: str) -> Optional[str]:
    """Parse and return the content of a .qasm file."""
    try:
        with open(file_path, 'r') as f:
            content = f.read().strip()
        
        if not content:
            print(f"⚠️  Empty .qasm file: {file_path}")
            return None
        
        return content
    except Exception as e:
        print(f"❌ Error reading .qasm file {file_path}: {e}")
        return None

def create_circuit_from_qasm(qasm_content: str):
    """Create a Qiskit QuantumCircuit from QASM content."""
    try:
        from qiskit import QuantumCircuit
        
        # Convert QASM string directly to QuantumCircuit
        circuit = QuantumCircuit.from_qasm_str(qasm_content)
        return circuit
    except Exception as e:
        print(f"❌ Error parsing QASM content: {e}")
        return None

def run_test():
    """Run the test_ibm_api.py script."""
    test_script = Path(__file__).parent / "test_ibm_api.py"
    if not test_script.exists():
        print("❌ test_ibm_api.py not found")
        return False
    
    print("🧪 Running IBM Quantum API test...")
    print("=" * 50)
    
    try:
        import subprocess
        result = subprocess.run([sys.executable, str(test_script)], 
                              capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

def select_backend_interactively(service) -> Optional[Any]:
    """Allow user to interactively select a backend."""
    try:
        backends = service.backends(operational=True)
        if not backends:
            print("❌ No operational backends available")
            return None
        
        print("📋 Available backends:")
        for i, backend in enumerate(backends):
            status = backend.status()
            status_icon = "🟢" if status.operational else "🔴"
            print(f"  {i+1}. {status_icon} {backend.name}")
            print(f"     - Qubits: {backend.num_qubits}")
            print(f"     - Operational: {status.operational}")
            print(f"     - Pending jobs: {getattr(status, 'pending_jobs', 'N/A')}")
            print(f"     - Simulator: {backend.simulator}")
            print()
        
        while True:
            try:
                choice = input(f"Select backend (1-{len(backends)}) or 'q' to quit: ").strip()
                if choice.lower() == 'q':
                    return None
                
                index = int(choice) - 1
                if 0 <= index < len(backends):
                    return backends[index]
                else:
                    print(f"❌ Please enter a number between 1 and {len(backends)}")
            except ValueError:
                print("❌ Please enter a valid number or 'q' to quit")
            except KeyboardInterrupt:
                print("\n❌ Cancelled by user")
                return None
                
    except Exception as e:
        print(f"❌ Error getting backends: {e}")
        return None

def execute_circuit_on_ibm(circuit, config: Dict[str, Any], shots: int = 1024, 
                          backend_name: Optional[str] = None, interactive: bool = False, 
                          json_output: bool = False) -> Dict[str, Any]:
    """Execute a quantum circuit on IBM Quantum Platform."""
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService, Sampler
        
        # Get API key from config or environment variable
        api_key = config.get('ibm_api_key') or os.environ.get('QISKIT_IBM_TOKEN') or os.environ.get('IBM_API_KEY')
        if not api_key:
            print("❌ No IBM Quantum API key found in config.json or environment variables")
            return {"success": False, "error": "No IBM Quantum API key found in config.json or environment variables"}
        
        print("🔑 Authenticating with IBM Quantum...")
        service = QiskitRuntimeService(channel="ibm_quantum_platform", token=api_key)
        
        # Select backend
        if backend_name:
            try:
                backend = service.backend(backend_name)
                print(f"✓ Using specified backend: {backend.name}")
            except Exception as e:
                print(f"❌ Backend '{backend_name}' not found: {e}")
                return {"success": False, "error": f"Backend '{backend_name}' not found: {e}"}
        elif interactive:
            # Interactive backend selection
            backend = select_backend_interactively(service)
            if backend is None:
                print("❌ No backend selected")
                return {"success": False, "error": "No backend selected"}
            print(f"✓ Using selected backend: {backend.name}")
        else:
            # Get first available backend
            print("🎯 Getting available backends...")
            backends = service.backends(operational=True)
            if not backends:
                print("❌ No operational backends available")
                return {"success": False, "error": "No operational backends available"}
            
            # Show available backends and use the first one
            print("📋 Available backends:")
            for i, backend in enumerate(backends):
                status = backend.status()
                status_icon = "🟢" if status.operational else "🔴"
                print(f"  {i+1}. {status_icon} {backend.name}")
                print(f"     - Qubits: {backend.num_qubits}")
                print(f"     - Operational: {status.operational}")
                print(f"     - Pending jobs: {getattr(status, 'pending_jobs', 'N/A')}")
                print(f"     - Simulator: {backend.simulator}")
                print()
            
            # Use the first available backend
            backend = backends[0]
            print(f"✓ Using backend: {backend.name}")
        
        # Display backend info
        status = backend.status()
        print(f"📊 Backend info:")
        print(f"   - Qubits: {backend.num_qubits}")
        print(f"   - Operational: {status.operational}")
        print(f"   - Pending jobs: {getattr(status, 'pending_jobs', 'N/A')}")
        print(f"   - Simulator: {backend.simulator}")
        
        # Transpile circuit for the target backend
        print("🔄 Transpiling circuit for target backend...")
        from qiskit import transpile
        transpiled_circuit = transpile(circuit, backend=backend)
        print(f"✓ Circuit transpiled: {transpiled_circuit.num_qubits} qubits, {transpiled_circuit.depth()} depth")
        
        # Execute circuit using Sampler
        print(f"🚀 Submitting job with {shots} shots...")
        sampler = Sampler(mode=backend)
        job = sampler.run([transpiled_circuit], shots=shots)
        print(f"✓ Job submitted successfully! Job ID: {job.job_id()}")
        
        # Wait for completion
        print("⏳ Waiting for job completion...")
        start_time = time.time()
        timeout = 600  # 10 minutes timeout
        
        while job.status() not in ['DONE', 'ERROR', 'CANCELLED']:
            if time.time() - start_time > timeout:
                print("⚠️  Job timeout - cancelling job")
                try:
                    job.cancel()
                except:
                    pass
                return {"success": False, "error": "Job timeout", "job_id": job.job_id()}
            
            print(f"   Status: {job.status()}")
            time.sleep(15)  # Check every 15 seconds
        
        if job.status() == 'DONE':
            print("✅ Job completed successfully!")
            
            # Get and display results
            result = job.result()
            print("📊 Results:")
            
            # Prepare results data
            results_data = []
            
            # Try to get measurement results from the result
            if hasattr(result, '_pub_results') and result._pub_results:
                pub_result = result._pub_results[0]
                
                if hasattr(pub_result, 'data'):
                    # Try to access data through items() method
                    if hasattr(pub_result.data, 'items'):
                        try:
                            data_items = list(pub_result.data.items())
                            
                            # Look for measurement data in the data items
                            for key, value in data_items:
                                # Handle BitArray (raw measurement results)
                                if key == 'c' and hasattr(value, 'get_counts'):
                                    counts = value.get_counts()
                                    print("   Measurement outcomes:")
                                    
                                    # Sort by count (descending)
                                    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
                                    
                                    for outcome, count in sorted_counts:
                                        probability = count / shots
                                        print(f"     |{outcome}⟩: {count} counts ({probability:.4f} = {probability*100:.2f}%)")
                                        
                                        results_data.append({
                                            "outcome": outcome,
                                            "probability": float(probability),
                                            "percentage": float(probability * 100),
                                            "count": int(count)
                                        })
                                    break
                                
                                # Handle quasi_dists
                                elif key == 'quasi_dists' and value:
                                    quasi_dists = value
                                    if quasi_dists:
                                        quasi_dist = quasi_dists[0]
                                        print("   Measurement outcomes:")
                                        
                                        # Sort by probability (descending)
                                        sorted_outcomes = sorted(quasi_dist.items(), 
                                                               key=lambda x: x[1], reverse=True)
                                        
                                        for outcome, probability in sorted_outcomes:
                                            # Determine number of qubits from circuit
                                            num_qubits = circuit.num_qubits
                                            binary = format(outcome, f'0{num_qubits}b')
                                            print(f"     |{binary}⟩: {probability:.4f} ({probability*100:.2f}%)")
                                            
                                            results_data.append({
                                                "outcome": binary,
                                                "probability": float(probability),
                                                "percentage": float(probability * 100),
                                                "count": int(probability * shots)
                                            })
                                        break
                        except Exception as e:
                            if not json_output:
                                print(f"   Error accessing measurement results: {e}")
            
            # Fallback: try to get counts from result
            if not results_data and hasattr(result, 'get_counts'):
                counts = result.get_counts()
                print("   Measurement outcomes (from counts):")
                
                # Sort by count (descending)
                sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
                
                for outcome, count in sorted_counts:
                    probability = count / shots
                    print(f"     |{outcome}⟩: {count} counts ({probability:.4f} = {probability*100:.2f}%)")
                    
                    results_data.append({
                        "outcome": outcome,
                        "probability": float(probability),
                        "percentage": float(probability * 100),
                        "count": int(count)
                    })
            
            if not results_data:
                print("   No measurement results found")
                # Add a placeholder result to indicate the circuit ran successfully
                results_data = [{
                    "outcome": "N/A",
                    "probability": 0.0,
                    "percentage": 0.0,
                    "count": 0,
                    "note": "Circuit executed successfully but no measurement results available"
                }]
            
            # Prepare metadata
            metadata = {
                "job_id": job.job_id(),
                "backend": {
                    "name": backend.name,
                    "qubits": backend.num_qubits,
                    "operational": status.operational,
                    "pending_jobs": getattr(status, 'pending_jobs', 'N/A'),
                    "simulator": backend.simulator
                },
                "circuit": {
                    "original_qubits": circuit.num_qubits,
                    "original_clbits": circuit.num_clbits,
                    "transpiled_qubits": transpiled_circuit.num_qubits,
                    "transpiled_depth": transpiled_circuit.depth()
                },
                "execution": {
                    "shots": shots,
                    "start_time": datetime.fromtimestamp(start_time).isoformat(),
                    "completion_time": datetime.now().isoformat(),
                    "duration_seconds": time.time() - start_time
                }
            }
            
            return {
                "success": True,
                "results": results_data,
                "metadata": metadata
            }
        else:
            print(f"❌ Job failed with status: {job.status()}")
            return {"success": False, "error": f"Job failed with status: {job.status()}", "job_id": job.job_id()}
            
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("💡 Install required packages: pip install qiskit qiskit-ibm-runtime")
        return {"success": False, "error": f"Missing required package: {e}"}
    except Exception as e:
        print(f"❌ Error executing circuit: {e}")
        return {"success": False, "error": f"Error executing circuit: {e}"}

def list_available_backends(config: Dict[str, Any]) -> bool:
    """List all available IBM Quantum backends."""
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService
        
        api_key = config.get('ibm_api_key') or os.environ.get('QISKIT_IBM_TOKEN') or os.environ.get('IBM_API_KEY')
        if not api_key:
            print("❌ No IBM Quantum API key found in config.json or environment variables")
            return False
        
        print("🔑 Connecting to IBM Quantum...")
        service = QiskitRuntimeService(channel="ibm_quantum_platform", token=api_key)
        
        print("📡 Fetching available backends...")
        backends = service.backends()
        
        if not backends:
            print("⚠️  No backends available")
            return False
        
        print(f"✓ Found {len(backends)} available backends:")
        print()
        
        # Group backends by type
        simulators = []
        real_devices = []
        
        for backend in backends:
            try:
                status = backend.status()
                is_operational = status.operational
                pending_jobs = getattr(status, 'pending_jobs', 'N/A')
                
                backend_info = {
                    'name': backend.name,
                    'qubits': backend.num_qubits,
                    'operational': is_operational,
                    'pending_jobs': pending_jobs,
                    'simulator': backend.simulator
                }
                
                if backend.simulator:
                    simulators.append(backend_info)
                else:
                    real_devices.append(backend_info)
                    
            except Exception as e:
                print(f"  ⚠️  {backend.name} - Error getting status: {e}")
        
        # Display simulators
        if simulators:
            print("🖥️  SIMULATORS:")
            for backend in simulators:
                status_icon = "🟢" if backend['operational'] else "🔴"
                print(f"  {status_icon} {backend['name']}")
                print(f"    - Qubits: {backend['qubits']}")
                print(f"    - Operational: {backend['operational']}")
                print(f"    - Pending jobs: {backend['pending_jobs']}")
                print()
        
        # Display real devices
        if real_devices:
            print("🔬 REAL QUANTUM DEVICES:")
            for backend in real_devices:
                status_icon = "🟢" if backend['operational'] else "🔴"
                print(f"  {status_icon} {backend['name']}")
                print(f"    - Qubits: {backend['qubits']}")
                print(f"    - Operational: {backend['operational']}")
                print(f"    - Pending jobs: {backend['pending_jobs']}")
                print()
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("💡 Install required packages: pip install qiskit qiskit-ibm-runtime")
        return False
    except Exception as e:
        print(f"❌ Error listing backends: {e}")
        return False

def interactive_setup(config: Dict[str, Any]) -> Dict[str, Any]:
    """Interactive setup for shots, backend, and response format."""
    print("🚀 IBM Quantum QASM Runner - Interactive Setup")
    print("=" * 50)
    
    # Get shots
    while True:
        try:
            shots_input = input("Enter number of shots (0-10000, default 1024): ").strip()
            if not shots_input:
                shots = 1024
                break
            shots = int(shots_input)
            if 0 <= shots <= 10000:
                break
            else:
                print("❌ Please enter a number between 0 and 10000")
        except ValueError:
            print("❌ Please enter a valid number")
        except KeyboardInterrupt:
            print("\n❌ Cancelled by user")
            sys.exit(1)
    
    # Get backend
    print("\n🔍 Searching for available backends...")
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService
        
        api_key = config.get('ibm_api_key') or os.environ.get('QISKIT_IBM_TOKEN') or os.environ.get('IBM_API_KEY')
        if not api_key:
            print("❌ No IBM Quantum API key found in config.json or environment variables")
            sys.exit(1)
        
        service = QiskitRuntimeService(channel="ibm_quantum_platform", token=api_key)
        backends = service.backends(operational=True)
        
        if not backends:
            print("❌ No operational backends available")
            sys.exit(1)
        
        print(f"\n📋 Found {len(backends)} available backends:")
        for i, backend in enumerate(backends):
            status = backend.status()
            status_icon = "🟢" if status.operational else "🔴"
            print(f"  {i+1}. {status_icon} {backend.name}")
            print(f"     - Qubits: {backend.num_qubits}")
            print(f"     - Operational: {status.operational}")
            print(f"     - Pending jobs: {getattr(status, 'pending_jobs', 'N/A')}")
            print(f"     - Simulator: {backend.simulator}")
            print()
        
        while True:
            try:
                choice = input(f"Select backend (1-{len(backends)}) or 'q' to quit: ").strip()
                if choice.lower() == 'q':
                    print("❌ Cancelled by user")
                    sys.exit(1)
                
                index = int(choice) - 1
                if 0 <= index < len(backends):
                    selected_backend = backends[index].name
                    break
                else:
                    print(f"❌ Please enter a number between 1 and {len(backends)}")
            except ValueError:
                print("❌ Please enter a valid number or 'q' to quit")
            except KeyboardInterrupt:
                print("\n❌ Cancelled by user")
                sys.exit(1)
                
    except Exception as e:
        print(f"❌ Error getting backends: {e}")
        sys.exit(1)
    
    # Get response format
    print("\n📊 Response Format Options:")
    print("  1. Human-readable (default)")
    print("  2. JSON format")
    print()
    
    while True:
        try:
            format_choice = input("Select response format (1-2, default 1): ").strip()
            if not format_choice:
                json_output = False
                break
            if format_choice == '1':
                json_output = False
                break
            elif format_choice == '2':
                json_output = True
                break
            else:
                print("❌ Please enter 1 or 2")
        except KeyboardInterrupt:
            print("\n❌ Cancelled by user")
            sys.exit(1)
    
    # Get visualization option
    print("\n🎨 Visualization Options:")
    print("  1. No visualization (default)")
    print("  2. Generate circuit diagram")
    print()
    
    while True:
        try:
            viz_choice = input("Select visualization option (1-2, default 1): ").strip()
            if not viz_choice:
                visualize = False
                break
            if viz_choice == '1':
                visualize = False
                break
            elif viz_choice == '2':
                visualize = True
                break
            else:
                print("❌ Please enter 1 or 2")
        except KeyboardInterrupt:
            print("\n❌ Cancelled by user")
            sys.exit(1)
    
    # Get JSON file saving option
    print("\n💾 JSON File Saving:")
    print("  1. Don't save to file (default)")
    print("  2. Save results to JSON file")
    print()
    
    while True:
        try:
            save_choice = input("Save to JSON file? (1-2, default 1): ").strip()
            if not save_choice:
                save_json = False
                break
            if save_choice == '1':
                save_json = False
                break
            elif save_choice == '2':
                save_json = True
                break
            else:
                print("❌ Please enter 1 or 2")
        except KeyboardInterrupt:
            print("\n❌ Cancelled by user")
            sys.exit(1)
    
    print(f"\n✅ Configuration:")
    print(f"   - Shots: {shots}")
    print(f"   - Backend: {selected_backend}")
    print(f"   - Format: {'JSON' if json_output else 'Human-readable'}")
    print(f"   - Visualization: {'Circuit diagram' if visualize else 'None'}")
    print(f"   - Save JSON: {'Yes' if save_json else 'No'}")
    print()
    
    return {
        'shots': shots,
        'backend': selected_backend,
        'json': json_output,
        'visualize': visualize,
        'save_json': save_json
    }

def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Execute .qasm files on IBM Quantum Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Interactive mode
  %(prog)s circuit.qasm                       # Run circuit.qasm with default settings
  %(prog)s circuit.qasm --shots 2048          # Run with 2048 shots
  %(prog)s circuit.qasm --backend ibm_brisbane  # Use specific backend
  %(prog)s circuit.qasm --interactive         # Interactively select backend
  %(prog)s circuit.qasm --json                # Output results in JSON format
  %(prog)s --test                             # Run API connection test
  %(prog)s --list-backends                    # List available backends
  %(prog)s circuit1.qasm circuit2.qasm        # Run multiple circuits
        """
    )
    
    parser.add_argument('qasm_files', nargs='*', 
                       help='.qasm files to execute')
    parser.add_argument('--shots', type=int, default=1024,
                       help='Number of shots to run (default: 1024)')
    parser.add_argument('--backend', type=str,
                       help='Specific backend to use (e.g., ibm_brisbane)')
    parser.add_argument('--interactive', action='store_true',
                       help='Interactively select backend')
    parser.add_argument('--json', action='store_true',
                       help='Output results in JSON format')
    parser.add_argument('--visualize', action='store_true',
                       help='Generate circuit diagram visualization')
    parser.add_argument('--save-json', action='store_true',
                       help='Save results to JSON file')
    parser.add_argument('--test', action='store_true',
                       help='Run IBM Quantum API connection test')
    parser.add_argument('--list-backends', action='store_true',
                       help='List all available backends')
    parser.add_argument('--non-interactive', action='store_true',
                       help='Run in non-interactive mode (auto-select first available backend)')
    
    args = parser.parse_args()
    
    # Check if running in a non-interactive environment (e.g., CI/CD)
    is_non_interactive = not sys.stdin.isatty() or args.non_interactive
    
    # Load configuration
    config = load_config()
    
    # Handle test flag
    if args.test:
        success = run_test()
        sys.exit(0 if success else 1)
    
    # Handle list backends flag
    if args.list_backends:
        success = list_available_backends(config)
        sys.exit(0 if success else 1)
    
    # Interactive mode - always run interactive setup unless specific flags are used
    if not args.test and not args.list_backends:
        # Only show welcome message in interactive mode
        if not is_non_interactive or not args.qasm_files:
            print("🚀 Welcome to IBM Quantum QASM Runner!")
        
        # If no .qasm files provided, get them interactively (or fail in non-interactive mode)
        if not args.qasm_files:
            if is_non_interactive:
                print("❌ No .qasm files specified")
                print("💡 Usage: qasm_runner.py <file.qasm> [options]")
                sys.exit(1)
            
            print("No .qasm files specified. Starting interactive mode...")
            print()
            
            # Get .qasm files
            while True:
                try:
                    files_input = input("Enter .qasm file path(s) (space-separated): ").strip()
                    if not files_input:
                        print("❌ No files specified")
                        continue
                    
                    files = files_input.split()
                    valid_files = []
                    for file_path in files:
                        if validate_qasm_file(file_path):
                            valid_files.append(file_path)
                    
                    if valid_files:
                        args.qasm_files = valid_files
                        break
                    else:
                        print("❌ No valid .qasm files found")
                except KeyboardInterrupt:
                    print("\n❌ Cancelled by user")
                    sys.exit(1)
        else:
            if not is_non_interactive:
                print("Starting interactive setup for provided files...")
                print()
        
        # Interactive setup for shots, backend, and format (only if not in non-interactive mode and not explicitly set)
        # Skip interactive setup if we're in non-interactive mode or if interactive flag is explicitly set
        if not is_non_interactive and (args.interactive or not args.backend):
            interactive_config = interactive_setup(config)
            if not args.backend:
                args.backend = interactive_config['backend']
            if not args.json:
                args.json = interactive_config['json']
            if args.shots == 1024:  # Default value, not specified by user
                args.shots = interactive_config['shots']
            if not args.visualize:
                args.visualize = interactive_config['visualize']
            if not args.save_json:
                args.save_json = interactive_config['save_json']
    
    # Validate all .qasm files and check qubit limits
    valid_files = []
    for file_path in args.qasm_files:
        if validate_qasm_file(file_path):
            # Check qubit limit before adding to valid files
            check_qubit_limit(file_path, config)
            valid_files.append(file_path)
    
    if not valid_files:
        print("❌ No valid .qasm files found")
        sys.exit(1)
    
    if not args.json:
        print(f"🚀 Processing {len(valid_files)} .qasm file(s)...")
        print("=" * 60)
    
    # Process each .qasm file
    success_count = 0
    all_results = []
    
    for i, file_path in enumerate(valid_files, 1):
        if not args.json:
            print(f"\n📁 Processing file {i}/{len(valid_files)}: {file_path}")
            print("-" * 40)
        
        # Parse QASM file
        qasm_content = parse_qasm_file(file_path)
        if not qasm_content:
            if args.json:
                all_results.append({
                    "file": file_path,
                    "success": False,
                    "error": "Failed to read QASM file"
                })
            continue
        
        # Create circuit from QASM
        circuit = create_circuit_from_qasm(qasm_content)
        if not circuit:
            if args.json:
                all_results.append({
                    "file": file_path,
                    "success": False,
                    "error": "Failed to create circuit from QASM"
                })
            continue
        
        if not args.json:
            print(f"✓ Circuit created: {circuit.num_qubits} qubits, {circuit.num_clbits} classical bits")
        
        # Generate circuit diagram if visualization is enabled
        diagram_path = ""
        if args.visualize:
            diagram_path = generate_circuit_diagram(circuit, file_path)
        
        # Execute circuit
        result = execute_circuit_on_ibm(circuit, config, args.shots, args.backend, args.interactive, args.json)
        
        # Add file information to result
        result["file"] = file_path
        
        # Add visualization info if diagram was generated
        if diagram_path:
            result["visualization"] = {
                "circuit_diagram": diagram_path
            }
        
        if result.get("success", False):
            success_count += 1
            if not args.json:
                print(f"✅ Successfully executed {file_path}")
        else:
            if not args.json:
                print(f"❌ Failed to execute {file_path}")
        
        all_results.append(result)
        
        # Save individual JSON file if enabled
        if args.save_json:
            # Create individual result for this file
            individual_result = {
                "summary": {
                    "file": file_path,
                    "timestamp": datetime.now().isoformat(),
                    "success": result.get("success", False)
                },
                "result": result
            }
            save_json_results(individual_result, file_path)
    
    # Output results
    if args.json:
        # JSON output
        json_output = {
            "summary": {
                "total_files": len(valid_files),
                "successful_files": success_count,
                "failed_files": len(valid_files) - success_count,
                "timestamp": datetime.now().isoformat()
            },
            "results": all_results
        }
        print(json.dumps(json_output, indent=2))
    else:
        # Human-readable output
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"✅ Successfully executed: {success_count}/{len(valid_files)} files")
        
        if success_count == len(valid_files):
            print("🎉 All circuits executed successfully!")
        else:
            print("⚠️  Some circuits failed to execute")
    
    # Exit with appropriate code
    if success_count == len(valid_files):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
