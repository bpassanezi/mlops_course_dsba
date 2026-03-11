import sys
import os

# Add 'src' and the root directory to sys.path so that tests can import modules
# from both locations.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
sys.path.insert(0, os.path.dirname(__file__))
