"""Kleine Hilfen für das XML einer Moodle-Sicherung."""
from __future__ import annotations

NULL = "$@NULL@$"  # SQL NULL in Moodle-Sicherungen (≠ leere Zeichenkette)


def x(text) -> str:
    """Text für einen XML-Knoten maskieren."""
    s = "" if text is None else str(text)
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def el(tag: str, wert) -> str:
    """Ein Element; None wird zu SQL NULL."""
    return f"<{tag}>{NULL if wert is None else x(wert)}</{tag}>"


def php(d: dict) -> str:
    """PHP serialize() für ein flaches dict aus str -> int/str."""
    teile = []
    for k, v in d.items():
        teile.append(f's:{len(k.encode())}:"{k}";')
        teile.append(f"i:{v};" if isinstance(v, int)
                     else f's:{len(str(v).encode())}:"{v}";')
    return f"a:{len(d)}:{{{''.join(teile)}}}"


def mime(name: str) -> str:
    endung = name.rsplit(".", 1)[-1].lower()
    return {
        "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "gif": "image/gif", "svg": "image/svg+xml", "webp": "image/webp",
        "pdf": "application/pdf", "html": "text/html", "htm": "text/html",
        "txt": "text/plain", "mp4": "video/mp4", "zip": "application/zip",
        "mp3": "audio/mp3", "m4a": "audio/mp4", "ogg": "audio/ogg", "wav": "audio/wav",  # mp3 wie Moodle
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }.get(endung, "application/octet-stream")
