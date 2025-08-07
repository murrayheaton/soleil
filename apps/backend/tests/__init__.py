
import os
import sys

# Ensure backend package is discoverable as 'app'
TESTS_DIR = os.path.dirname(__file__)
BACKEND_ROOT = os.path.abspath(os.path.join(TESTS_DIR, '..'))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)