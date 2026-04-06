"""Maestro session management: open, close, find."""

import re

from virtuoso_bridge import VirtuosoClient


def open_session(client: VirtuosoClient, lib: str, cell: str) -> str:
    """Open maestro in background via maeOpenSetup. Returns session string."""
    r = client.execute_skill(
        f'let((session) session = maeOpenSetup("{lib}" "{cell}" "maestro") '
        f'printf("[%s maeOpenSetup] %s/%s  session=%s\\n" nth(2 parseString(getCurrentTime())) "{lib}" "{cell}" session) '
        f'session)')
    session = (r.output or "").strip('"')
    if not session or session in ("nil", "t"):
        raise RuntimeError(f"maeOpenSetup failed for {lib}/{cell}")
    return session


def close_session(client: VirtuosoClient, session: str) -> None:
    """Close a background maestro session via maeCloseSession."""
    client.execute_skill(
        f'maeCloseSession(?session "{session}" ?forceClose t) '
        f'printf("[%s maeCloseSession] session=%s closed\\n" nth(2 parseString(getCurrentTime())) "{session}")')


def find_open_session(client: VirtuosoClient) -> str | None:
    """Find the first active session with a valid test. Returns session string or None."""
    raw = client.execute_skill('''
let((result)
  result = nil
  foreach(s maeGetSessions()
    unless(result
      when(maeGetSetup(?session s)
        result = s
      )
    )
  )
  result
)
''').output or ""
    session = raw.strip('"')
    if session and session != "nil":
        return session
    return None
