"""Network-free regression tests for temporary arXiv outages."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import arxiv
from requests.exceptions import ConnectionError, Timeout

from bots import arxiv_bot as bot


def http_error(status):
    return arxiv.HTTPError("https://export.arxiv.org/api/query", 0, status)


class QueryTests(unittest.TestCase):
    def setUp(self):
        self.sleep = patch.object(bot.time, "sleep").start()
        patch.object(bot.random, "uniform", return_value=0).start()
        self.addCleanup(patch.stopall)

    def test_client_disables_nested_retries_and_slows_pages(self):
        client = bot.make_client(page_size=30)
        self.assertEqual(client.num_retries, 0)
        self.assertEqual(client.delay_seconds, 10)
        self.assertEqual(client.page_size, 30)

    def test_recovers_from_503_then_429(self):
        paper = object()
        client = Mock()
        client.results.side_effect = [http_error(503), http_error(429), iter([paper])]
        self.assertEqual(bot.get_papers(client, "avatars", 30), [paper])
        self.assertEqual([call.args[0] for call in self.sleep.call_args_list], [10, 60, 120])
        search = client.results.call_args.args[0]
        self.assertEqual(search.max_results, 30)
        self.assertEqual(search.query, "avatars")

    def test_exhaustion_is_bounded(self):
        client = Mock()
        client.results.side_effect = http_error(429)
        with self.assertRaises(bot.ArxivUnavailableError):
            bot.get_papers(client, "avatars")
        self.assertEqual(client.results.call_count, 4)
        self.assertEqual([call.args[0] for call in self.sleep.call_args_list], [10, 60, 120, 240])

    def test_nonretryable_error_propagates(self):
        client = Mock()
        client.results.side_effect = http_error(400)
        with self.assertRaises(arxiv.HTTPError):
            bot.get_papers(client, "bad query")
        self.assertEqual(client.results.call_count, 1)

    def test_network_failures_are_retried(self):
        client = Mock()
        client.results.side_effect = [ConnectionError("offline"), Timeout("slow"), iter([])]
        self.assertEqual(bot.get_papers(client, "avatars"), [])
        self.assertEqual(client.results.call_count, 3)

    def test_generator_failure_retries_without_duplicate_results(self):
        paper = object()
        def interrupted():
            yield paper
            raise http_error(503)
        client = Mock()
        client.results.side_effect = [interrupted(), iter([paper])]
        self.assertEqual(bot.get_papers(client, "avatars"), [paper])


class DigestTests(unittest.TestCase):
    def run_digest(self, root, outcomes):
        paper = SimpleNamespace(entry_id="https://arxiv.org/abs/2601.00001v1",
                                pdf_url="https://arxiv.org/pdf/2601.00001v1", title="Kept paper")
        ranker = Mock()
        ranker.candidate_count.return_value = 30
        ranker.rank.return_value = [SimpleNamespace(result=paper, reason=lambda: "test")]
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test"}), \
             patch.object(bot, "PROJECT_DIR", Path(root)), \
             patch.object(bot, "PaperRanker", return_value=ranker), \
             patch.object(bot, "make_client"), \
             patch.object(bot, "get_papers", side_effect=outcomes) as query:
            path = bot.run_daily_digest(
                {"avatars": ["first", "second", "third"]}, 3,
                lambda url: {}, lambda summary: "Kept paper summary\n")
        self.assertEqual(query.call_count, 3)
        self.assertEqual(ranker.note_api_request.call_count, 3)
        return Path(path).read_text(encoding="utf-8")

    def test_failed_query_keeps_papers_and_continues(self):
        with TemporaryDirectory() as root:
            text = self.run_digest(root, [[object()], bot.ArxivUnavailableError("offline"), []])
        self.assertIn("Kept paper summary", text)
        self.assertIn("**Query unavailable:**", text)
        self.assertIn("### third", text)
        self.assertEqual(text.count("(No results)"), 1)

    def test_all_queries_failed_return_an_explicitly_incomplete_report(self):
        with TemporaryDirectory() as root:
            text = self.run_digest(root, [bot.ArxivUnavailableError("offline")] * 3)
        self.assertEqual(text.count("**Query unavailable:**"), 3)
        self.assertNotIn("(No results)", text)


if __name__ == "__main__":
    unittest.main()
