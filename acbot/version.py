# SPDX-FileCopyrightText: 2026 Vadym Yemelianov (AuthorChe / VadymYem), AuthorBot integration and maintenance
# SPDX-License-Identifier: AGPL-3.0-only
# Existing upstream copyright and license notices are retained; see NOTICE.md and LICENSE.

"""Represents current userbot version"""
# ©️ AuthorChe, 2022-2026
# This file is a part of AuthorBot Userbot
# 🌐 https://github.com/VadymYem/AuthorBot
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html
# I glad to see you here
__version__ = (1, 10, 13)

import os

import git

try:
    branch = git.Repo(
        path=os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    ).active_branch.name
except Exception:
    branch = "main"
