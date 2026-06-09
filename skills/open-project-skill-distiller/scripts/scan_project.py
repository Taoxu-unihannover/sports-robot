#!/usr/bin/env python3
"""Scan a project and output tech stack map - skill script."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from plugins.ball_project_assimilator.scripts.scan_project import main

if __name__ == "__main__":
    main()
