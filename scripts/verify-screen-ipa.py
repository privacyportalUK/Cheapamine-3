#!/usr/bin/env python3
"""Compatibility entrypoint for the current package IPA verifier."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name("verify-package-ipa.py")), run_name="__main__")
