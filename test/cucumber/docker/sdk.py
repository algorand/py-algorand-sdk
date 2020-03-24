#!/usr/bin/env python3

import subprocess
import sys

default_dirs = { 
    'features_dir': '/opt/py-algorand-sdk/test/cucumber/features',
    'source': '/opt/py-algorand-sdk',
    'docker': '/opt/py-algorand-sdk/test/cucumber/docker',
    'test': '/opt/py-algorand-sdk/test/cucumber'
}

def setup_sdk():
    """
    Setup python cucumber environment.
    """    
    pass

def test_sdk():
    sys.stdout.flush()
    subprocess.check_call(['behave %s -f progress2' % default_dirs['test']], shell=True)