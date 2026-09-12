"""Source adapter: a file uploaded into a Slack channel.

The gotcha that costs people twenty minutes: the file_shared event does NOT
contain the file. It carries an id. You call files_info, then fetch
url_private_download with an Authorization: Bearer header. Without the header
Slack returns an HTML login page rather than an error, so it reads as a parsing
bug.
"""
from __future__ import annotations

import logging

import requests

from .. import config
from ..models import Source

log = logging.getLogger("ameen.slack")

_TIMEOUT = 30
_RETRIES = 3


def fetch(client, file_id: str, channel_id: str, user_id: str) -> tuple[bytes, str, Source]:
    info = client.files_info(file=file_id)
    f = info["file"]
    filename = f.get("name") or f.get("title") or "document"
    url = f.get("url_private_download") or f.get("url_private")
    if not url:
        raise RuntimeError("Slack returned no private download URL for this file")

    headers = {"Authorization": f"Bearer {config.SLACK_BOT_TOKEN}"}
    last: Exception | None = None
    for attempt in range(_RETRIES):
        try:
            resp = requests.get(url, headers=headers, timeout=_TIMEOUT)
            resp.raise_for_status()
            body = resp.content
            # Without the auth header Slack serves a sign-in page with HTTP 200.
            if body[:15].lstrip().lower().startswith(b"<!doctype html"):
                raise RuntimeError(
                    "Slack returned an HTML page instead of the file: the bot token is "
                    "missing the files:read scope, or the app was not reinstalled after "
                    "the scope was added."
                )
            return body, filename, Source(
                kind="slack",
                channel_id=channel_id,
                user_id=user_id,
                file_id=file_id,
                filename=filename,
            )
        except Exception as exc:  # noqa: BLE001 - retried, then surfaced
            last = exc
    raise RuntimeError(f"could not download the file after {_RETRIES} attempts: {last}")


def channel_history(client, channel_id: str, limit: int = 200, max_pages: int = 5) -> list[dict]:
    """Everything said in this channel, so Ameen can find what was promised."""
    messages: list[dict] = []
    cursor = None
    for _ in range(max_pages):
        kwargs = {"channel": channel_id, "limit": limit}
        if cursor:
            kwargs["cursor"] = cursor
        res = client.conversations_history(**kwargs)
        messages += res.get("messages", [])
        if not res.get("has_more"):
            break
        cursor = (res.get("response_metadata") or {}).get("next_cursor")
        if not cursor:
            break
    return messages


def permalink_getter(client, channel_id: str):
    """Returns a function ts -> permalink, cached, and never raising.

    Injected into the memory module so that module never touches Slack and can
    be tested offline.
    """
    cache: dict[str, str] = {}

    def get(ts: str) -> str:
        if not ts:
            return ""
        if ts in cache:
            return cache[ts]
        try:
            link = client.chat_getPermalink(channel=channel_id, message_ts=ts)["permalink"]
        except Exception as exc:  # noqa: BLE001 - a missing permalink degrades to no link
            # quietly even though we degrade to a finding with no link.
            log.warning("could not build a permalink for ts=%s: %s", ts, exc)
            link = ""
        cache[ts] = link
        return link

    return get
