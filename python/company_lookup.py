"""Fetch one public company. Requires Python 3.10+ and MART_API_KEY."""

import argparse
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen


def company_lookup(url: str) -> dict:
    key = os.environ.get("MART_API_KEY", "").strip()
    if not key:
        raise ValueError("Set MART_API_KEY before making a request.")
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname not in {"linkedin.com", "www.linkedin.com"}
            or not parsed.path.startswith("/company/") or not parsed.path[9:].strip("/")
            or parsed.username or parsed.password or parsed.port):
        raise ValueError("Use a public https://www.linkedin.com/company/... URL.")
    query = urlencode({"type": "company", "url": url})
    request = Request(
        "https://api.mart.dev/v1/linkedin?" + query,
        headers={"x-api-key": key, "Accept": "application/json"},
    )
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Public LinkedIn company URL")
    args = parser.parse_args()
    try:
        print(json.dumps(company_lookup(args.url), indent=2, ensure_ascii=False))
        return 0
    except HTTPError as exc:
        delay = exc.headers.get("Retry-After")
        print(f"Mart returned HTTP {exc.code}." +
              (f" Retry-After: {delay}." if delay else ""), file=sys.stderr)
    except (ValueError, URLError, TimeoutError, OSError):
        print("Request failed. Check the company URL, MART_API_KEY and network connection.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
