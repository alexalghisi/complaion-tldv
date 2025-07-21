#!/usr/bin/env python3
"""
Setup script for Complaion tl;dv Integration Backend
"""
import os
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_python_version():
    """Check if Python version is compatible"""
    required_version = (3, 11)
    current_version = sys.version_info[:2]

    if current_version < required_version:
        print(f"  Python {required_version[0]}.{required_version[1]}+ is required")
        print(f"   Current version: {current_version[0]}.{current_version[1]}")
        return False

    print(f"  Python version: {current_version[0]}.{current_version[1]}")
    return True

def create_virtual_environment():
    """Create virtual environment if it doesn't exist"""
    venv_path = Path("venv")

    if venv_path.exists():
        print("  Virtual environment already exists")
        return True

    try:
        print("  Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("  Virtual environment created")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  Failed to create virtual environment: {e}")
        return False

def get_pip_executable():
    """Get the correct pip executable path"""
    if os.name == 'nt':  # Windows
        return Path("venv/Scripts/pip")
    else:  # Unix/Linux/macOS
        return Path("venv/bin/pip")

def install_dependencies():
    """Install Python dependencies"""
    pip_exe = get_pip_executable()

    if not pip_exe.exists():
        print("pip executable not found in virtual environment")
        return False

    try:
        print("Installing dependencies...")
        subprocess.run([
            str(pip_exe), "install", "-r", "requirements.txt"
        ], check=True)
        print("Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        return False

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_file = Path(".env")
    parent_env = Path("../.env")

    env_path = None
    if env_file.exists():
        env_path = env_file
    elif parent_env.exists():
        env_path = parent_env

    if not env_path:
        print("  .env file not found")
        print("   Please copy .env.example to .env and configure it")
        return False

    # Check required variables
    required_vars = ['TLDV_API_KEY', 'FIREBASE_PROJECT_ID', 'SECRET_KEY']
    missing_vars = []

    with open(env_path, 'r') as f:
        content = f.read()
        for var in required_vars:
            if f"{var}=" not in content or f"{var}=your-" in content:
                missing_vars.append(var)

    if missing_vars:
        print(f"  Missing or unconfigured variables in {env_path}:")
        for var in missing_vars:
            print(f"   - {var}")
        print("   Please configure these variables before running the application")
        return False

    print(f" Environment file configured: {env_path}")
    return True

def check_firebase_service_account():
    """Check if Firebase service account file exists"""
    service_account_paths = [
        Path("firebase-service-account.json"),
        Path("../firebase-service-account.json")
    ]

    for path in service_account_paths:
        if path.exists():
            print(f" Firebase service account found: {path}")
            return True

    print(" Firebase service account file not found")
    print("   Please download your service account key from Firebase Console")
    print("   and save it as 'firebase-service-account.json'")
    return False

def run_tests():
    """Run the test suite"""
    try:
        print("Running tests...")
        python_exe = Path("venv/bin/python") if os.name != 'nt' else Path("venv/Scripts/python")

        result = subprocess.run([
            str(python_exe), "test_api.py"
        ], capture_output=True, text=True)

        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)

        if result.returncode == 0:
            print("All tests passed!")
            return True
        else:
            print("Some tests failed")
            return False

    except subprocess.CalledProcessError as e:
        print(f" Failed to run tests: {e}")
        return False
    except FileNotFoundError:
        print("️  Could not run tests - Python executable not found")
        return False

def display_next_steps():
    """Display next steps for the user"""
    print("\n" + "="*50)
    print(" Setup Complete!")
    print("="*50)
    print("\n Next Steps:")
    print("\n1. Activate virtual environment:")
    if os.name == 'nt':  # Windows
        print("   venv\\Scripts\\activate")
    else:  # Unix/Linux/macOS
        print("   source venv/bin/activate")

    print("\n2. Run the application:")
    print("   python app.py")

    print("\n3. Test the API:")
    print("   curl http://localhost:5000/health")

    print("\n4. View API documentation:")
    print("   http://localhost:5000/api/")

    print("\n Useful Commands:")
    print("   python test_api.py        # Run tests")
    print("   python app.py             # Start development server")
    print("   gunicorn app:create_app() # Start production server")

    print("\n Configuration Files:")
    print("   .env                      # Environment variables")
    print("   firebase-service-account.json # Firebase credentials")
    print("   requirements.txt          # Python dependencies")

def main():
    """Main setup function"""
    print(" Complaion tl;dv Integration Backend Setup")
    print("="*50)

    steps = [
        ("Python Version", check_python_version),
        ("Virtual Environment", create_virtual_environment),
        ("Dependencies", install_dependencies),
        ("Environment Configuration", check_env_file),
        ("Firebase Service Account", check_firebase_service_account),
    ]

    results = {}

    for step_name, step_func in steps:
        print(f"\ {step_name}...")
        try:
            results[step_name] = step_func()
        except Exception as e:
            print(f" {step_name} failed: {e}")
            results[step_name] = False

    # Summary
    print(f"\n{'='*50}")
    print(" Setup Summary:")

    passed = 0
    total = len(results)

    for step_name, result in results.items():
        status = "✅ OK" if result else " FAILED"
        print(f"   {step_name}: {status}")
        if result:
            passed += 1

    print(f"\nSetup: {passed}/{total} steps completed")

    if passed == total:
        print("\nRunning validation tests...")
        test_passed = run_tests()

        if test_passed:
            display_next_steps()
            return 0
        else:
            print("\n Setup completed but some tests failed.")
            print("   Please check the configuration and try again.")
            return 1
    else:
        print(f"\n Setup incomplete. Please fix the failed steps and run again.")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)