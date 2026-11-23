"""Email drafting — NOVA writes the email, user reviews and sends.

Actual sending needs Gmail API + OAuth (planned). For now we produce a
ready-to-send draft plus a mailto: link that opens the user's mail app
with subject/body prefilled.
"""

import re
from urllib.parse import quote

PREFIXES = ("write email", "write a email", "write an email", "draft email",
            "compose email", "email to", "email ", "gmail ", "mail to",
            "mail ", "send email", "send a email", "send an email")


def looks_like_email_command(message: str) -> bool:
    low = message.lower().strip()
    return any(low.startswith(p) for p in PREFIXES)


def _strip_prefix(message: str) -> str:
    low = message.lower().strip()
    for p in PREFIXES:
        if low.startswith(p):
            return message.strip()[len(p):].strip()
    return message.strip()


def draft_email(message: str, llm, memories: dict | None = None) -> str | None:
    """Return a formatted draft reply, or None if drafting failed."""
    topic = _strip_prefix(message)
    if not topic:
        topic = "a quick update"

    contacts = ""
    if memories:
        mails = {k: v for k, v in memories.items()
                 if re.search(r"mail|email", k, re.I)}
        if mails:
            contacts = "\nKnown contacts (use if relevant):\n" + "\n".join(
                f"- {k}: {v}" for k, v in list(mails.items())[:5])

    prompt = (
        "Write a short, professional email.\n"
        f"Topic/request: {topic}\n"
        "Format exactly:\n"
        "Subject: <one line>\n\n"
        "<greeting>\n\n"
        "<2-4 sentence body>\n\n"
        "<sign-off>\n"
        "Do not write explanations — output only the email." + contacts
    )
    try:
        draft = llm.think(prompt, None,
                          tone_hint="Output only the email text, no commentary.")
    except Exception:
        return None
    if not draft or len(draft.strip()) < 20:
        return None

    draft = draft.strip()
    # Split subject for mailto link
    m = re.match(r"(?is)subject:\s*(.+?)\n\n?(.*)", draft)
    subject, body = (m.group(1).strip(), m.group(2).strip()) if m else ("", draft)
    mailto = f"mailto:?subject={quote(subject)}&body={quote(body)}"

    lines = ["**Draft email ready** — review, then send:\n", "```", draft, "```", "",
             f"[Open in your mail app]({mailto})"]
    return "\n".join(lines)
