"""
Test installation functions.
"""

import os
import pytest
import shutil

import stanza

pytestmark = [pytest.mark.travis, pytest.mark.client]

def test_install_corenlp():
    test_dir = "./test-corenlp-latest"
    # we do not reset the CORENLP_HOME variable since this may impact the 
    # client tests
    stanza.install_corenlp(dir=test_dir)

    assert os.path.isdir(test_dir), "Installation destination directory not found."
    jar_files = [f for f in os.listdir(test_dir) \
        if f.endswith('.jar') and f.startswith('stanford-corenlp')]
    assert len(jar_files) > 0, \
        "Cannot find stanford-corenlp jar files in the installation directory."
    assert not os.path.exists(os.path.join(test_dir, 'corenlp.zip')), \
        "Downloaded zip file was not removed."
    
    # cleanup after test
    shutil.rmtree(test_dir)
