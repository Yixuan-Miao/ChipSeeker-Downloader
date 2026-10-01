import json
import os
import unittest
from pathlib import Path

from chipseeker_downloader.browser import candidate_urls
from chipseeker_downloader.manifest import find_latest_manifest, load_manifest
from chipseeker_downloader.naming import paper_filename, safe_component


class DownloaderCoreTests(unittest.TestCase):
    def test_ieee_candidate_prefers_direct_pdf_endpoint(self):
        urls = candidate_urls(
            {
                "pdf_url": "https://ieeexplore.ieee.org/stamp/stamp.jsp?arnumber=123456",
                "article_number": "123456",
            }
        )
        self.assertEqual(
            urls[0],
            "https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber=123456",
        )

    def test_filename_is_windows_safe(self):
        name = paper_filename({"title": 'A/B: Test? "Paper"', "year": "2026", "doi": "10.1/a"})
        self.assertTrue(name.endswith(".pdf"))
        self.assertNotIn("/", name)
        self.assertNotIn(":", name)

    def test_manifest_load(self):
        path = Path(__file__).parent / "_manifest_test.csdl"
        try:
            path.write_text(
                json.dumps(
                    {
                        "format": "chipseeker-download-task",
                        "version": 1,
                        "papers": [{"title": "Paper", "pdf_url": "https://example.com/a.pdf"}],
                    }
                ),
                encoding="utf-8",
            )
            task = load_manifest(path)
            self.assertEqual(task["papers"][0]["title"], "Paper")
        finally:
            path.unlink(missing_ok=True)

    def test_find_latest_manifest(self):
        root = Path(__file__).parent
        older = root / "_older_test.csdl"
        newer = root / "_newer_test.csdl"
        try:
            older.write_text("{}", encoding="utf-8")
            newer.write_text("{}", encoding="utf-8")
            old_time = older.stat().st_mtime - 10
            os.utime(older, (old_time, old_time))
            self.assertEqual(find_latest_manifest(root), newer)
        finally:
            older.unlink(missing_ok=True)
            newer.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()

