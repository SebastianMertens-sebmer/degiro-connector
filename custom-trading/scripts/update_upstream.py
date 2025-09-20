#!/usr/bin/env python3
"""
Update script to sync with upstream degiro-connector changes
Keeps the custom-trading API updated with latest DEGIRO connector features
"""

import subprocess
import sys
from pathlib import Path


def run_command(command: str, cwd: Path = None) -> tuple[bool, str]:
    """Run a shell command and return success status and output"""
    try:
        result = subprocess.run(
            command.split(),
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr


def main():
    """Update the degiro-connector dependency from upstream"""
    
    print("🔄 Updating DEGIRO Connector from Upstream")
    print("=" * 50)
    
    # Get to the project root (parent of custom-trading)
    project_root = Path(__file__).parent.parent.parent
    custom_trading_dir = project_root / "custom-trading"
    
    print(f"📁 Project root: {project_root}")
    print(f"📁 Custom trading: {custom_trading_dir}")
    
    # Step 1: Update the main repository from upstream
    print("\n1️⃣ Fetching latest changes from upstream...")
    success, output = run_command("git fetch upstream", cwd=project_root)
    if not success:
        print(f"❌ Failed to fetch upstream: {output}")
        return False
    print("✅ Fetched upstream changes")
    
    # Step 2: Check if there are new commits
    success, output = run_command("git log HEAD..upstream/main --oneline", cwd=project_root)
    if output.strip():
        print(f"\n📋 New upstream commits:")
        print(output)
        
        print("\n2️⃣ Merging upstream changes...")
        success, output = run_command("git merge upstream/main", cwd=project_root)
        if not success:
            print(f"❌ Failed to merge upstream: {output}")
            print("🔧 You may need to resolve conflicts manually")
            return False
        print("✅ Merged upstream changes")
    else:
        print("✅ Already up to date with upstream")
    
    # Step 3: Update the Python package dependency
    print("\n3️⃣ Updating degiro-connector Python package...")
    venv_python = custom_trading_dir / "venv" / "bin" / "python"
    
    if venv_python.exists():
        # Use virtual environment
        success, output = run_command(
            f"{venv_python} -m pip install --upgrade git+https://github.com/Chavithra/degiro-connector.git",
            cwd=custom_trading_dir
        )
    else:
        # Use system python
        success, output = run_command(
            "pip3 install --upgrade git+https://github.com/Chavithra/degiro-connector.git",
            cwd=custom_trading_dir
        )
    
    if not success:
        print(f"❌ Failed to update Python package: {output}")
        return False
    print("✅ Updated degiro-connector Python package")
    
    # Step 4: Test the API still works
    print("\n4️⃣ Testing API imports...")
    test_script = custom_trading_dir / "tests" / "test_subtype_filtering.py"
    if test_script.exists():
        if venv_python.exists():
            success, output = run_command(f"{venv_python} {test_script}", cwd=custom_trading_dir)
        else:
            success, output = run_command(f"python3 {test_script}", cwd=custom_trading_dir)
        
        if success:
            print("✅ API imports working correctly")
        else:
            print(f"⚠️ API test failed: {output}")
            print("🔧 Check for breaking changes in degiro-connector")
    
    print("\n🎉 Update complete!")
    print("\n📋 Next steps:")
    print("1. Test your API endpoints")
    print("2. Update any code if there are breaking changes")
    print("3. Deploy to production if all tests pass")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)