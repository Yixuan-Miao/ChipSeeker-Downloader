import os
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from .naming import is_pdf_file, paper_filename, unique_path


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
MAX_PDF_BYTES = 250 * 1024 * 1024


class StopRequested(RuntimeError):
    pass


def _is_https_url(value):
    try:
        parsed = urlparse(str(value or ""))
    except ValueError:
        return False
    return parsed.scheme == "https" and bool(parsed.hostname)


def candidate_urls(paper, discovered_urls=None, current_url=""):
    urls = []

    def add(value):
        value = str(value or "").strip()
        if _is_https_url(value) and value not in urls:
            urls.append(value)

    for value in discovered_urls or []:
        add(value)
    add(current_url)
    original = str(paper.get("pdf_url") or "").strip()
    article_number = str(paper.get("article_number") or "").strip()
    if not article_number:
        match = re.search(r"(?:arnumber=|/document/)(\d+)", original)
        article_number = match.group(1) if match else ""
    if article_number and "ieeexplore.ieee.org" in original:
        add(f"https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber={article_number}")
    if "nature.com/articles/" in original and ".pdf" not in original.lower():
        add(original.rstrip("/") + ".pdf")
    add(original)
    add(paper.get("fallback_url"))
    return urls


class BrowserDownloader:
    def __init__(self, profile_dir, browser="auto", timeout_seconds=45):
        self.profile_dir = Path(profile_dir).expanduser().resolve()
        self.browser = browser
        self.timeout_ms = max(10, int(timeout_seconds)) * 1000
        self.playwright = None
        self.context = None

    def __enter__(self):
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.playwright = sync_playwright().start()
        channels = [self.browser] if self.browser != "auto" else ["msedge", "chrome"]
        errors = []
        for channel in channels:
            try:
                self.context = self.playwright.chromium.launch_persistent_context(
                    user_data_dir=str(self.profile_dir),
                    channel=channel,
                    headless=False,
                    accept_downloads=True,
                    viewport=None,
                    args=["--start-maximized"],
                )
                break
            except PlaywrightError as exc:
                errors.append(f"{channel}: {exc}")
        if self.context is None:
            self.playwright.stop()
            raise RuntimeError(
                "Could not start Microsoft Edge or Google Chrome. "
                "Install one of them, then run the downloader again.\n" + "\n".join(errors)
            )
        return self

    def __exit__(self, exc_type, exc, traceback):
        if self.context is not None:
            self.context.close()
        if self.playwright is not None:
            self.playwright.stop()

    def _requests_session(self, url):
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/pdf,*/*;q=0.8"})
        try:
            cookies = self.context.cookies([url])
        except PlaywrightError:
            cookies = []
        for cookie in cookies:
            session.cookies.set(
                cookie.get("name", ""),
                cookie.get("value", ""),
                domain=cookie.get("domain") or None,
                path=cookie.get("path") or "/",
            )
        return session

    def _fetch_pdf(self, url, target_path, referer=""):
        temporary_path = target_path.with_suffix(target_path.suffix + ".part")
        if temporary_path.exists():
            temporary_path.unlink()
        session = self._requests_session(url)
        headers = {"Referer": referer} if _is_https_url(referer) else {}
        try:
            with session.get(url, headers=headers, stream=True, allow_redirects=True, timeout=(20, 120)) as response:
                response.raise_for_status()
                content_length = int(response.headers.get("Content-Length") or 0)
                if content_length > MAX_PDF_BYTES:
                    return False, f"PDF exceeds {MAX_PDF_BYTES // (1024 * 1024)} MB"
                total = 0
                first = b""
                with temporary_path.open("wb") as handle:
                    for chunk in response.iter_content(chunk_size=1024 * 256):
                        if not chunk:
                            continue
                        if not first:
                            first = chunk[:1024]
                            if b"%PDF-" not in first:
                                return False, f"Response is not a PDF ({response.headers.get('Content-Type', 'unknown')})"
                        total += len(chunk)
                        if total > MAX_PDF_BYTES:
                            return False, f"PDF exceeds {MAX_PDF_BYTES // (1024 * 1024)} MB"
                        handle.write(chunk)
                if total < 1024 or not is_pdf_file(temporary_path):
                    return False, "Downloaded file failed PDF validation"
                os.replace(temporary_path, target_path)
                return True, f"{total / (1024 * 1024):.1f} MB"
        except (OSError, requests.RequestException, ValueError) as exc:
            return False, str(exc)
        finally:
            if temporary_path.exists():
                temporary_path.unlink()

    def download_paper(self, paper, output_dir, interactive=True):
        target = unique_path(output_dir, paper_filename(paper))
        original_url = str(paper.get("pdf_url") or paper.get("fallback_url") or "").strip()
        if not _is_https_url(original_url):
            return {"status": "failed", "reason": "No usable HTTPS URL", "path": ""}

        page = self.context.new_page()
        discovered = []
        downloads = []

        def observe_response(response):
            content_type = str(response.headers.get("content-type") or "").lower()
            if "application/pdf" in content_type and response.url not in discovered:
                discovered.append(response.url)

        page.on("response", observe_response)
        page.on("download", lambda download: downloads.append(download))

        try:
            try:
                page.goto(original_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            except PlaywrightTimeoutError:
                pass
            except PlaywrightError as exc:
                if "download" not in str(exc).lower():
                    print(f"  Browser navigation warning: {exc}")
            page.wait_for_timeout(2500)

            while True:
                if downloads:
                    try:
                        downloads[-1].save_as(str(target))
                        if is_pdf_file(target):
                            return {"status": "downloaded", "reason": "browser download", "path": str(target)}
                        if target.exists():
                            target.unlink()
                    except PlaywrightError as exc:
                        print(f"  Browser download warning: {exc}")

                frame_urls = [frame.url for frame in page.frames if _is_https_url(frame.url)]
                for candidate in candidate_urls(
                    paper,
                    discovered_urls=[*discovered, *frame_urls],
                    current_url=page.url,
                ):
                    ok, detail = self._fetch_pdf(candidate, target, referer=page.url)
                    if ok:
                        return {"status": "downloaded", "reason": detail, "path": str(target), "url": candidate}

                if not interactive:
                    return {
                        "status": "failed",
                        "reason": f"No PDF detected; current page: {page.url}",
                        "path": "",
                    }

                print("\n  The current page is not a downloadable PDF.")
                print(f"  Browser page: {page.url}")
                print("  Fix IEEE login, VPN, or the page in the visible browser.")
                try:
                    choice = input("  Press Enter to retry, S to skip, or Q to stop: ").strip().lower()
                except EOFError:
                    choice = "s"
                if choice == "q":
                    raise StopRequested("Stopped by user")
                if choice == "s":
                    return {"status": "failed", "reason": f"Skipped at {page.url}", "path": ""}
                page.wait_for_timeout(1000)
        finally:
            page.close()

