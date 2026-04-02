"""Shim for imghdr module removed in Python 3.13+. Needed by tweepy 4.14."""


def what(file, h=None):
    """Minimal imghdr.what implementation for tweepy compatibility."""
    if h is None:
        if isinstance(file, (str, bytes)):
            with open(file, "rb") as f:
                h = f.read(32)
        else:
            location = file.tell()
            h = file.read(32)
            file.seek(location)

    if h[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if h[:3] == b"GIF":
        return "gif"
    if h[:2] in (b"\xff\xd8", b"\xff\xe0", b"\xff\xe1"):
        return "jpeg"
    if h[:4] == b"RIFF" and h[8:12] == b"WEBP":
        return "webp"
    return None
