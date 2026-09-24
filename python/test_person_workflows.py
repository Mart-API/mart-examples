import copy
import io
import os
import unittest
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

import person_workflows as workflows


URL = "https://www.linkedin.com/in/example-contact"
SNAPSHOT = {
    "type": "linkedin-refresh", "url": URL, "accessible": True,
    "currentTitle": "Engineer", "titleSource": "linkedin", "companyState": "public",
    "currentCompany": {"name": "Example Company", "linkedInId": "123"},
}


class PersonWorkflowTests(unittest.TestCase):
    def compare(self, latest):
        return workflows.compare_refresh(copy.deepcopy(SNAPSHOT), latest, URL)["changesForReview"]

    def test_missing_fields_do_not_mean_departure(self):
        latest = dict(SNAPSHOT, currentTitle=None, currentCompany=None, companyState="unknown")
        self.assertEqual(self.compare(latest), [])

    def test_inaccessible_profile_does_not_mean_change(self):
        self.assertEqual(self.compare(dict(SNAPSHOT, accessible=False, currentTitle="Different")), [])

    def test_company_rename_with_same_id_does_not_mean_move(self):
        latest = dict(SNAPSHOT, currentCompany={"name": "New Brand", "linkedInId": "123"})
        self.assertEqual(self.compare(latest), [])

    def test_restricted_company_is_not_compared(self):
        latest = dict(SNAPSHOT, companyState="restricted", currentCompany={"name": "Other", "linkedInId": "456"})
        self.assertEqual(self.compare(latest), [])

    def test_possible_changes_preserve_source_and_both_snapshots(self):
        before = copy.deepcopy(SNAPSHOT)
        latest = dict(SNAPSHOT, currentTitle="Lead Engineer", titleSource="headline",
                      currentCompany={"name": "Other Company", "linkedInId": "456"})
        result = workflows.compare_refresh(before, latest, URL)
        self.assertEqual([c["field"] for c in result["changesForReview"]], ["currentTitle", "currentCompany"])
        self.assertEqual(result["changesForReview"][0]["afterSource"], "headline")
        self.assertEqual(before, SNAPSHOT)
        self.assertEqual(result["previous"], SNAPSHOT)
        self.assertEqual(result["latest"], latest)

    def test_different_person_snapshot_is_rejected(self):
        with self.assertRaises(ValueError):
            workflows.compare_refresh(SNAPSHOT, {}, "https://www.linkedin.com/in/different-contact")

    def test_meeting_posts_failure_preserves_profile(self):
        profile = {"accessible": True, "profile": {"name": "Example Contact"}}
        with patch.object(workflows, "fetch_person", side_effect=[profile, TimeoutError]):
            result = workflows.meeting_prep(URL)
        self.assertEqual(result["profileResponse"], profile)
        self.assertEqual(result["postsResponse"]["status"], "unavailable")

    def test_meeting_inaccessible_profile_skips_posts(self):
        with patch.object(workflows, "fetch_person", return_value={"accessible": False}) as fetch:
            result = workflows.meeting_prep(URL)
        fetch.assert_called_once_with("profile", URL)
        self.assertEqual(result["postsResponse"]["status"], "skipped_profile_unavailable")

    def test_post_limit_and_key_placement(self):
        with patch.dict(os.environ, {"MART_API_KEY": "fixture-key"}), patch.object(workflows, "urlopen") as request:
            request.return_value.__enter__.return_value = io.BytesIO(b'{"posts": []}')
            workflows.fetch_person("posts", URL)
        req = request.call_args.args[0]
        params = parse_qs(urlsplit(req.full_url).query)
        self.assertEqual(params, {"type": ["posts"], "url": [URL], "limit": ["3"]})
        self.assertEqual(req.get_header("X-api-key"), "fixture-key")
        self.assertNotIn("fixture-key", req.full_url)
        self.assertEqual(request.call_args.kwargs["timeout"], 30)

    def test_missing_key_does_not_make_request(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(workflows, "urlopen") as request:
            with self.assertRaises(ValueError):
                workflows.fetch_person("profile", URL)
            request.assert_not_called()

    def test_rate_limit_is_reported_without_retry_or_key(self):
        error = HTTPError("https://api.mart.dev/v1/linkedin", 429, "Limited", {"Retry-After": "3"}, None)
        with patch.dict(os.environ, {"MART_API_KEY": "fixture-key"}), \
                patch.object(workflows, "urlopen", side_effect=error) as request, \
                patch("sys.argv", ["person_workflows.py", "enrich", URL]), \
                patch("sys.stderr", new_callable=io.StringIO) as output:
            self.assertEqual(workflows.main(), 1)
        self.assertEqual(request.call_count, 1)
        self.assertIn("Retry-After: 3", output.getvalue())
        self.assertNotIn("fixture-key", output.getvalue())


if __name__ == "__main__":
    unittest.main()
