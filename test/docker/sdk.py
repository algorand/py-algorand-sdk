#!/usr/bin/env python3

import subprocess
import sys

default_dirs = { 
    'features_dir': '/opt/py-algorand-sdk/test/features',
    'source': '/opt/py-algorand-sdk',
    'docker': '/opt/py-algorand-sdk/test/docker'
}

def setup_sdk():
    """
    Setup python cucumber environment.
    """    
    pass

def test_sdk():
    sys.stdout.flush()
    
    subprocess.check_call(['behave test -f progress2'], shell=True)
    # subprocess.check_call(['mvn test -Dcucumber.options="--tags @template"'], shell=True, cwd=sdk.default_dirs['cucumber'])
    # subprocess.check_call(['mvn test -Dcucumber.options="/opt/sdk-testing/features/template.feature"'], shell=True, cwd=sdk.default_dirs['cucumber'])
