"""Public-profile enrichment, contact refresh and meeting preparation source data."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, unquote
from urllib.request import Request, urlopen


def profile_identity(url):
    parsed = urlsplit(url)
    parts = parsed.path.strip("/").split("/")
    if (parsed.scheme != "https" or parsed.hostname not in {"www.linkedin.com", "linkedin.com"}
            or parsed.username or parsed.password or parsed.port
            or len(parts) != 2 or parts[0] != "in" or not parts[1]):
        raise ValueError("Use a public https://www.linkedin.com/in/... URL.")
    return unquote(parts[1]).lower()


def fetch_person(kind, url):
    profile_identity(url)
    key = os.environ.get("MART_API_KEY", "").strip()
    if not key:
        raise ValueError("Set MART_API_KEY before making a request.")
    params = {"type": kind, "url": url}
    if kind == "posts":
        params["limit"] = 3
    request = Request("https://api.mart.dev/v1/linkedin?" + urlencode(params),
                      headers={"x-api-key": key, "Accept": "application/json"})
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def compare_refresh(previous, latest, requested_url):
    """Report possible differences without writing over a contact record."""
    previous_url = previous.get("url")
    if not previous_url or profile_identity(previous_url) != profile_identity(requested_url):
        raise ValueError("The previous snapshot must belong to the same requested profile URL.")
    if previous.get("type") != "linkedin-refresh":
        raise ValueError("Provide a saved Refresh response as the previous snapshot.")
    changes = []
    if previous.get("accessible") is True and latest.get("accessible") is True:
        before, after = previous.get("currentTitle"), latest.get("currentTitle")
        if before and after and before.strip().casefold() != after.strip().casefold():
            changes.append({"field": "currentTitle", "before": before, "after": after,
                            "beforeSource": previous.get("titleSource"),
                            "afterSource": latest.get("titleSource")})
        old_company, new_company = previous.get("currentCompany") or {}, latest.get("currentCompany") or {}
        if previous.get("companyState") == latest.get("companyState") == "public":
            for field in ("linkedInId", "linkedInUrl", "name"):
                before, after = old_company.get(field), new_company.get(field)
                if before and after:
                    normalize = lambda value: str(value).strip().rstrip("/").casefold()
                    if normalize(before) != normalize(after):
                        changes.append({"field": "currentCompany", "comparedBy": field,
                                        "before": old_company, "after": new_company})
                    break
    return {"previous": previous, "latest": latest, "changesForReview": changes,
            "note": "Possible differences only. Missing fields are not departures; keep previous values until reviewed."}


def meeting_prep(url):
    profile = fetch_person("profile", url)
    posts = {"posts": [], "status": "skipped_profile_unavailable"}
    if profile.get("accessible") is True:
        try:
            posts = fetch_person("posts", url)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError):
            posts = {"posts": [], "status": "unavailable"}
    return {"requestedUrl": url, "fetchedAt": datetime.now(timezone.utc).isoformat(),
            "profileResponse": profile, "postsResponse": posts,
            "note": "Source material for meeting preparation. Public posts may be incomplete. No generated claims or personal assessment."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workflow", choices=["enrich", "refresh", "meeting-prep"])
    parser.add_argument("url", help="Public LinkedIn profile URL")
    parser.add_argument("--previous", type=Path, help="Saved Refresh JSON, only for refresh")
    args = parser.parse_args()
    if args.previous and args.workflow != "refresh":
        parser.error("--previous is only supported for refresh")
    try:
        previous = json.loads(args.previous.read_text()) if args.previous else None
        if previous is not None:
            compare_refresh(previous, {}, args.url)
        if args.workflow == "meeting-prep":
            result = meeting_prep(args.url)
        else:
            result = fetch_person("profile" if args.workflow == "enrich" else "refresh", args.url)
            if previous is not None:
                result = compare_refresh(previous, result, args.url)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except HTTPError as error:
        delay = error.headers.get("Retry-After")
        print(f"Mart returned HTTP {error.code}." + (f" Retry-After: {delay}." if delay else ""), file=sys.stderr)
    except (ValueError, URLError, TimeoutError, OSError, TypeError, AttributeError):
        print("Request failed. Check your key, profile URL, network and previous snapshot format.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
