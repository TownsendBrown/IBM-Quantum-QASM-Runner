#!/usr/bin/env python3
"""
IBM Quantum API Key Test Program
Tests IBM Quantum API key connectivity and functionality.
"""

import json
import sys
import time
from datetime import datetime

def load_api_key_from_config():
    """Load API key from config.json file."""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        api_key = config.get('ibm_api_key', '')
        if not api_key or api_key == 'YOUR_IBM_QUANTUM_API_KEY':
            return None
        return api_key
    except FileNotFoundError:
        print("❌ config.json file not found")
        return None
    except json.JSONDecodeError:
        print("❌ Invalid JSON in config.json")
        return None

def load_api_key_from_file(filename):
    """Load API key from a separate JSON file."""
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        # Try different possible key names
        for key_name in ['ibm_api_key', 'api_key', 'token', 'key']:
            if key_name in data:
                return data[key_name]
        print(f"❌ No API key found in {filename}")
        return None
    except FileNotFoundError:
        print(f"❌ File {filename} not found")
        return None
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in {filename}")
        return None

def validate_api_key_format(api_key):
    """Validate IBM Quantum API key format."""
    print("🔍 Validating API key format...")
    
    if not api_key:
        print("❌ API key is empty")
        return False
    
    if len(api_key) < 40:
        print(f"⚠️  API key seems short ({len(api_key)} characters)")
        print("💡 IBM Quantum API keys are typically 40+ characters")
        return False
    
    if not api_key.replace('_', '').replace('-', '').isalnum():
        print("⚠️  API key contains unexpected characters")
        print("💡 IBM Quantum API keys typically contain only letters, numbers, _ and -")
        return False
    
    print(f"✓ API key format looks valid ({len(api_key)} characters)")
    return True

def test_ibm_quantum_connection(api_key):
    """Test connection to IBM Quantum services."""
    print("🔧 Testing IBM Quantum API connection...")
    
    # First validate the API key format
    if not validate_api_key_format(api_key):
        return False
    
    try:
        # Import IBM Quantum Runtime
        from qiskit_ibm_runtime import QiskitRuntimeService
        
        print("✓ IBM Quantum Runtime imported successfully")
        
        # Initialize service with API key
        print("🔑 Authenticating with IBM Quantum...")
        service = QiskitRuntimeService(channel="ibm_quantum_platform", token=api_key)
        
        print("✓ Authentication successful!")
        
        # Get available backends
        print("📡 Fetching available backends...")
        backends = service.backends()
        
        if not backends:
            print("⚠️  No backends available")
            return False
        
        print(f"✓ Found {len(backends)} available backends:")
        
        # Display backend information
        operational_backends = []
        for backend in backends[:10]:  # Show first 10 backends
            try:
                status = backend.status()
                is_operational = status.operational
                pending_jobs = status.pending_jobs if hasattr(status, 'pending_jobs') else 'N/A'
                
                status_icon = "🟢" if is_operational else "🔴"
                print(f"  {status_icon} {backend.name}")
                print(f"    - Operational: {is_operational}")
                print(f"    - Qubits: {backend.num_qubits}")
                print(f"    - Pending jobs: {pending_jobs}")
                
                if is_operational:
                    operational_backends.append(backend)
                    
            except Exception as e:
                print(f"  ⚠️  {backend.name} - Error getting status: {e}")
        
        if len(backends) > 10:
            print(f"  ... and {len(backends) - 10} more backends")
        
        print(f"\n✅ Operational backends: {len(operational_backends)}")
        
        # Test getting least busy backend
        if operational_backends:
            print("\n🎯 Finding least busy backend...")
            try:
                least_busy = service.least_busy(operational=True, simulator=False)
                print(f"✓ Least busy backend: {least_busy.name}")
                print(f"  - Qubits: {least_busy.num_qubits}")
                
                # Get more detailed info
                status = least_busy.status()
                print(f"  - Pending jobs: {getattr(status, 'pending_jobs', 'N/A')}")
                
            except Exception as e:
                print(f"⚠️  Could not determine least busy backend: {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import IBM Quantum Runtime: {e}")
        print("💡 Make sure qiskit-ibm-runtime is installed:")
        print("   pip install qiskit-ibm-runtime")
        return False
        
    except Exception as e:
        error_msg = str(e).lower()
        if "invalid token" in error_msg or "authentication" in error_msg:
            print(f"❌ Authentication failed: Invalid API key")
            print("💡 Please check your IBM Quantum API key")
            print("🔗 Get a new key from: https://quantum-computing.ibm.com/")
        elif "network" in error_msg or "connection" in error_msg or "resolve" in error_msg:
            print(f"❌ Network error: Cannot connect to IBM Quantum")
            print("💡 This could be due to:")
            print("   - No internet connection")
            print("   - Firewall blocking access")
            print("   - IBM Quantum services temporarily unavailable")
            print("   - DNS resolution issues")
            print("🔧 Try again later or check your network connection")
        else:
            print(f"❌ Unexpected error: {e}")
        return False

def test_simple_circuit(api_key):
    """Test running a simple quantum circuit on IBM Quantum."""
    print("\n🧪 Testing simple quantum circuit execution...")
    
    try:
        from qiskit import QuantumCircuit
        from qiskit_ibm_runtime import QiskitRuntimeService, Sampler
        
        # Create a simple 2-qubit Bell state circuit
        qc = QuantumCircuit(2, 2)
        qc.h(0)  # Hadamard gate on qubit 0
        qc.cx(0, 1)  # CNOT gate
        qc.measure_all()
        
        print("✓ Created simple Bell state circuit")
        
        # Initialize service
        service = QiskitRuntimeService(channel="ibm_quantum_platform", token=api_key)
        
        # Get a backend (preferably simulator for testing)
        backends = service.backends(simulator=True, operational=True)
        if not backends:
            # Fall back to real hardware if no simulators
            backends = service.backends(operational=True)
            
        if not backends:
            print("❌ No operational backends available")
            return False
            
        backend = backends[0]  # Use first available backend
        print(f"✓ Using backend: {backend.name}")
        
        # Create sampler and run circuit
        print("🚀 Submitting job to IBM Quantum...")
        sampler = Sampler(backend=backend)
        
        # Run with fewer shots for faster testing
        job = sampler.run([qc], shots=100)
        print(f"✓ Job submitted successfully! Job ID: {job.job_id()}")
        
        # Wait for job completion (with timeout)
        print("⏳ Waiting for job completion...")
        start_time = time.time()
        timeout = 300  # 5 minutes timeout
        
        while job.status().name not in ['DONE', 'ERROR', 'CANCELLED']:
            if time.time() - start_time > timeout:
                print("⚠️  Job timeout - cancelling job")
                try:
                    job.cancel()
                except:
                    pass
                return False
                
            print(f"   Status: {job.status().name}")
            time.sleep(10)  # Check every 10 seconds
        
        if job.status().name == 'DONE':
            print("✅ Job completed successfully!")
            
            # Get results
            result = job.result()
            print("📊 Results received:")
            
            # Display quasi-distribution
            if hasattr(result, 'quasi_dists') and result.quasi_dists:
                quasi_dist = result.quasi_dists[0]
                print("   Measurement outcomes:")
                for outcome, probability in quasi_dist.items():
                    binary = format(outcome, '02b')
                    print(f"     |{binary}⟩: {probability:.3f}")
            
            return True
        else:
            print(f"❌ Job failed with status: {job.status().name}")
            return False
            
    except Exception as e:
        print(f"❌ Circuit test failed: {e}")
        return False

def main():
    """Main function to test IBM Quantum API key."""
    print("=" * 60)
    print("IBM Quantum API Key Test")
    print("=" * 60)
    
    # Try to get API key from various sources
    api_key = None
    
    # Method 1: Command line argument
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
        print(f"📝 Using API key from command line")
    
    # Method 2: config.json file
    if not api_key:
        api_key = load_api_key_from_config()
        if api_key:
            print(f"📝 Using API key from config.json")
    
    # Method 3: apikey.json file (if exists)
    if not api_key:
        api_key = load_api_key_from_file('apikey.json')
        if api_key:
            print(f"📝 Using API key from apikey.json")
    
    # Method 4: Check Downloads folder for apikey.json
    if not api_key:
        import os
        downloads_path = os.path.expanduser('~/Downloads/apikey.json')
        if os.path.exists(downloads_path):
            api_key = load_api_key_from_file(downloads_path)
            if api_key:
                print(f"📝 Using API key from ~/Downloads/apikey.json")
    
    if not api_key:
        print("❌ No IBM Quantum API key found!")
        print("\n💡 You can provide the API key in several ways:")
        print("   1. Command line: python3 test_ibm_api.py YOUR_API_KEY")
        print("   2. Update config.json with your API key")
        print("   3. Create apikey.json with your API key")
        print("   4. Place apikey.json in ~/Downloads/")
        print("\n🔗 Get your API key from: https://quantum-computing.ibm.com/")
        return 1
    
    # Mask API key for display
    masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
    print(f"🔑 API Key: {masked_key}")
    
    # Test 1: Basic connection
    print(f"\n{'='*60}")
    print("TEST 1: Basic Connection & Authentication")
    print(f"{'='*60}")
    
    connection_success = test_ibm_quantum_connection(api_key)
    
    # If network failed, offer offline validation
    if not connection_success:
        print(f"\n{'='*60}")
        print("OFFLINE VALIDATION")
        print(f"{'='*60}")
        
        offline_valid = validate_api_key_format(api_key)
        if offline_valid:
            print("✅ API key format appears valid")
            print("💡 Network connection failed, but key format is correct")
            print("🔧 Try the test again when you have internet access")
        else:
            print("❌ API key format validation failed")
            print("💡 Please check your API key")
    
    if not connection_success:
        print("\n❌ Basic connection test failed!")
        return 1
    
    # Test 2: Simple circuit execution (optional)
    print(f"\n{'='*60}")
    print("TEST 2: Simple Circuit Execution (Optional)")
    print(f"{'='*60}")
    
    run_circuit = input("🤔 Run a simple quantum circuit? (y/N): ").lower().strip()
    
    if run_circuit in ['y', 'yes']:
        circuit_success = test_simple_circuit(api_key)
        if circuit_success:
            print("\n🎉 Circuit execution test passed!")
        else:
            print("\n⚠️  Circuit execution test failed (but connection works)")
    else:
        print("⏭️  Skipping circuit execution test")
    
    # Final summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print("✅ IBM Quantum API key is valid and working!")
    print("✅ Authentication successful")
    print("✅ Backend access confirmed")
    print(f"📅 Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Update config.json if needed
    if connection_success:
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            
            if config.get('ibm_api_key') == 'YOUR_IBM_QUANTUM_API_KEY':
                config['ibm_api_key'] = api_key
                config['backend'] = 1  # Set to use IBM Quantum
                
                with open('config.json', 'w') as f:
                    json.dump(config, f, indent=2)
                
                print("\n💾 Updated config.json with your API key")
                print("💡 You can now use backend=1 in your applications")
        except:
            pass  # Ignore errors in config update
    
    print("\n🚀 Your IBM Quantum API key is ready to use!")
    return 0

if __name__ == '__main__':
    sys.exit(main())
