"""Represents current AuthоrChe's version"""
__version__ = (1, 8, 5)

import git
import os

try:
    branch = git.Repo(
        path=os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    ).active_branch.name
except Exception:
    branch = "main"
