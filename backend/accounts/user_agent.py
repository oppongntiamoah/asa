"""
A tiny, dependency-free User-Agent parser — good enough to show "Chrome on
Windows" / "Safari on iPhone" next to a login session without pulling in a
full UA-parsing library for what's ultimately a cosmetic label.
"""
import re

_OS_PATTERNS = [
    (re.compile(r"iPhone"), "iPhone"),
    (re.compile(r"iPad"), "iPad"),
    (re.compile(r"Android"), "Android"),
    (re.compile(r"Windows NT"), "Windows"),
    (re.compile(r"Mac OS X"), "Mac"),
    (re.compile(r"Linux"), "Linux"),
]

# Order matters: Chrome/Edge/Opera UAs all also contain "Safari/", so those
# more specific tokens must be checked first.
_BROWSER_PATTERNS = [
    (re.compile(r"Edg/"), "Edge"),
    (re.compile(r"OPR/|Opera"), "Opera"),
    (re.compile(r"CriOS/"), "Chrome"),
    (re.compile(r"Chrome/"), "Chrome"),
    (re.compile(r"FxiOS/"), "Firefox"),
    (re.compile(r"Firefox/"), "Firefox"),
    (re.compile(r"Safari/"), "Safari"),
]


def describe_user_agent(user_agent: str) -> str:
    user_agent = user_agent or ""
    os_name = next((name for pattern, name in _OS_PATTERNS if pattern.search(user_agent)), None)
    browser = next((name for pattern, name in _BROWSER_PATTERNS if pattern.search(user_agent)), None)
    if browser and os_name:
        return f"{browser} on {os_name}"
    return browser or os_name or "Unknown device"


def is_mobile_user_agent(user_agent: str) -> bool:
    return bool(re.search(r"iPhone|iPad|Android|Mobile", user_agent or ""))


def get_client_ip(request) -> "str | None":
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
