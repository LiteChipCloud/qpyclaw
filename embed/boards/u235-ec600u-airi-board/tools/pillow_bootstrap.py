#!/usr/bin/env python
"""
Host-side helper to locate a workspace-local Pillow install.
"""

from __future__ import annotations

import site
import sys
from pathlib import Path


def ensure_pillow_path() -> bool:
    current = Path(__file__).resolve().parent
    checked = set()
    while True:
        local_site = current / ".pillow_local"
        key = str(local_site)
        if key not in checked:
            checked.add(key)
            try:
                if local_site.exists():
                    text = str(local_site)
                    if text not in sys.path:
                        sys.path.insert(0, text)
                    return True
            except Exception:
                pass
        if current.parent == current:
            break
        current = current.parent

    user_site = str(site.getusersitepackages() or "").strip()
    if user_site:
        candidate = Path(user_site)
        try:
            if candidate.exists() and user_site not in sys.path:
                sys.path.insert(0, user_site)
                return True
        except Exception:
            pass
    current = Path(__file__).resolve().parent
    while True:
        candidate = current / ".toolsite"
        key = str(candidate)
        if key not in checked:
            checked.add(key)
            try:
                if candidate.exists():
                    text = str(candidate)
                    if text not in sys.path:
                        sys.path.insert(0, text)
                    return True
            except Exception:
                pass
        if current.parent == current:
            break
        current = current.parent
    return False
