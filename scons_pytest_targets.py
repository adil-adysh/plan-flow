# SCons custom targets for PlanFlow
# Add this as a separate file to keep SConstruct clean.

import os
import sys

def run_pytest(args=None):
    """Run pytest with optional arguments."""
    import subprocess
    cmd = [sys.executable, '-m', 'pytest']
    if args:
        cmd.extend(args)
    return subprocess.call(cmd)

def run_pytest_integration():
    return run_pytest(['tests/integration'])

def run_pytest_unit():
    return run_pytest(['tests', '--ignore=tests/integration'])

def run_pytest_desktop_ui():
    return run_pytest(['tests/desktop_ui'])
