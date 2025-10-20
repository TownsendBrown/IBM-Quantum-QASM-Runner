#!/usr/bin/env python3
"""
AER Simulator QASM Runner CLI
A command-line tool to execute .qasm files on Qiskit AER Simulator.
"""

import argparse
import json
import sys
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

def load_config() -> Dict[str, Any]:
    """Load configuration from config.json file."""
    config_path = Path(__file__).parent / "config.json"
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ config.json file not found")
        print("💡 Please ensure config.json exists with qubit_limit configured")
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
        json_path = f"{qasm_filename}_aer_results_{timestamp}.json"
        
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

def execute_circuit_on_aer(circuit, shots: int = 1024, json_output: bool = False) -> Dict[str, Any]:
    """Execute a quantum circuit on AER Simulator."""
    try:
        from qiskit_aer import AerSimulator
        from qiskit import transpile
        import time
        
        # Create AER simulator
        print("🖥️  Initializing AER Simulator...")
        simulator = AerSimulator()
        
        # Transpile circuit for the simulator
        print("🔄 Transpiling circuit for AER Simulator...")
        transpiled_circuit = transpile(circuit, simulator)
        print(f"✓ Circuit transpiled: {transpiled_circuit.num_qubits} qubits, {transpiled_circuit.depth()} depth")
        
        # Execute circuit
        print(f"🚀 Running simulation with {shots} shots...")
        start_time = time.time()
        job = simulator.run(transpiled_circuit, shots=shots)
        result = job.result()
        execution_time = time.time() - start_time
        
        print(f"✅ Simulation completed in {execution_time:.2f} seconds!")
        
        # Get measurement results
        counts = result.get_counts()
        print("📊 Results:")
        
        # Prepare results data
        results_data = []
        
        # Sort by count (descending)
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        
        for outcome, count in sorted_counts:
            probability = count / shots
            print(f"   |{outcome}⟩: {count} counts ({probability:.4f} = {probability*100:.2f}%)")
            
            results_data.append({
                "outcome": outcome,
                "probability": float(probability),
                "percentage": float(probability * 100),
                "count": int(count)
            })
        
        # Prepare metadata
        metadata = {
            "backend": {
                "name": "AerSimulator",
                "type": "local_aer_simulator"
            },
            "circuit": {
                "original_qubits": circuit.num_qubits,
                "original_clbits": circuit.num_clbits,
                "transpiled_qubits": transpiled_circuit.num_qubits,
                "transpiled_depth": transpiled_circuit.depth()
            },
            "execution": {
                "shots": shots,
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": execution_time
            }
        }
        
        return {
            "success": True,
            "results": results_data,
            "metadata": metadata
        }
            
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("💡 Install required packages: pip install qiskit qiskit-aer")
        return {"success": False, "error": f"Missing required package: {e}"}
    except Exception as e:
        print(f"❌ Error executing circuit: {e}")
        return {"success": False, "error": f"Error executing circuit: {e}"}

def interactive_setup() -> Dict[str, Any]:
    """Interactive setup for shots and response format."""
    print("🚀 AER Simulator QASM Runner - Interactive Setup")
    print("=" * 50)
    
    # Get shots
    while True:
        try:
            shots_input = input("Enter number of shots (1-1000000, default 1024): ").strip()
            if not shots_input:
                shots = 1024
                break
            shots = int(shots_input)
            if 1 <= shots <= 1000000:
                break
            else:
                print("❌ Please enter a number between 1 and 1000000")
        except ValueError:
            print("❌ Please enter a valid number")
        except KeyboardInterrupt:
            print("\n❌ Cancelled by user")
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
    print(f"   - Backend: AerSimulator (local)")
    print(f"   - Format: {'JSON' if json_output else 'Human-readable'}")
    print(f"   - Visualization: {'Circuit diagram' if visualize else 'None'}")
    print(f"   - Save JSON: {'Yes' if save_json else 'No'}")
    print()
    
    return {
        'shots': shots,
        'json': json_output,
        'visualize': visualize,
        'save_json': save_json
    }

def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Execute .qasm files on Qiskit AER Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Interactive mode
  %(prog)s circuit.qasm                       # Run circuit.qasm with default settings
  %(prog)s circuit.qasm --shots 2048          # Run with 2048 shots
  %(prog)s circuit.qasm --json                # Output results in JSON format
  %(prog)s circuit.qasm --visualize           # Generate circuit diagram
  %(prog)s circuit1.qasm circuit2.qasm        # Run multiple circuits
        """
    )
    
    parser.add_argument('qasm_files', nargs='*', 
                       help='.qasm files to execute')
    parser.add_argument('--shots', type=int, default=1024,
                       help='Number of shots to run (default: 1024)')
    parser.add_argument('--json', action='store_true',
                       help='Output results in JSON format')
    parser.add_argument('--visualize', action='store_true',
                       help='Generate circuit diagram visualization')
    parser.add_argument('--save-json', action='store_true',
                       help='Save results to JSON file')
    
    args = parser.parse_args()
    
    # Load configuration (for qubit limit)
    config = load_config()
    
    # Interactive mode
    print("🚀 Welcome to AER Simulator QASM Runner!")
    
    # Track if files were provided via command line
    files_provided_via_cli = len(args.qasm_files) > 0
    
    # If no .qasm files provided, get them interactively
    if not args.qasm_files:
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
    
    # Interactive setup for shots and format (only if no files provided via CLI)
    if not files_provided_via_cli:
        print("Starting interactive setup...")
        print()
        # No files provided initially, run full interactive setup
        interactive_config = interactive_setup()
        args.json = interactive_config['json']
        args.shots = interactive_config['shots']
        args.visualize = interactive_config['visualize']
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
        
        # Execute circuit on AER
        result = execute_circuit_on_aer(circuit, args.shots, args.json)
        
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

