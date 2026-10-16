import os
import sys

# Make the local 'src' importable so we test the tombstone package in this repo.
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, src_dir)
