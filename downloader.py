import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from chipseeker_downloader.browser import BrowserDownloader, StopRequested
from chipseeker_downloader.manifest import ManifestError, find_latest_manifest, load_manifest
from chipseeker_downloader.naming import safe_component


def default_output_dir(task):
    name = safe_component(task.get("title"), fallback="ChipSeeker Download", limit=80)
    return Path.home() / "Downloads" / "ChipSeeker" / name


def write_report(output_dir, task, records):
    report = {
        "format": "chipseeker-download-report",
        "version": 1,
        "search_id": task.get("search_id", ""),
        "task_title": task.get("title", ""),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "downloaded": sum(item["status"] == "downloaded" for item in records),
        "failed": sum(item["status"] != "downloaded" for item in records),
        "items": records,
    }
    report_path = output_dir / "download_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    failed = [item for item in records if item["status"] != "downloaded"]
    failed_path = output_dir / "failed_downloads.md"
    if failed:
        lines = ["# Failed ChipSeeker Downloads", ""]
        for item in failed:
            lines.extend(
                [
                    f"## {item.get('title') or 'Untitled'}",
                    "",
                    f"- Reason: {item.get('reason', '')}",
                    f"- URL: {item.get('url', '')}",
                    "",
                ]
            )
        failed_path.write_text("\n".join(lines), encoding="utf-8")
    elif failed_path.exists():
        failed_path.unlink()
    return report_path, failed_path if failed else None


def parse_args():
    parser = argparse.ArgumentParser(description="Download PDFs from a ChipSeeker .csdl task.")
    parser.add_argument("task", nargs="?", help="Path to a .csdl task file")
    parser.add_argument("--latest", action="store_true", help="Use the newest .csdl under Downloads")
    parser.add_argument("--output", help="PDF output directory")
    parser.add_argument("--profile", default=str(Path(__file__).parent / "user_profile"))
    parser.add_argument("--browser", choices=("auto", "msedge", "chrome"), default="auto")
    parser.add_argument("--non-interactive", action="store_true", help="Skip failed pages instead of waiting for login")
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        task_path = find_latest_manifest() if args.latest else args.task
        if not task_path:
            raise ManifestError("Provide a .csdl file or use --latest.")
        task = load_manifest(task_path)
    except ManifestError as exc:
        print(f"Task error: {exc}", file=sys.stderr)
        return 2

    output_dir = Path(args.output).expanduser().resolve() if args.output else default_output_dir(task)
    output_dir.mkdir(parents=True, exist_ok=True)
    papers = task["papers"]

    print("ChipSeeker Downloader")
    print(f"Task: {task.get('title', 'ChipSeeker selection')}")
    print(f"Papers: {len(papers)}")
    print(f"Output: {output_dir}")
    print("A visible browser will open. Complete IEEE login or VPN access there when requested.\n")

    records = []
    stopped = False
    try:
        with BrowserDownloader(args.profile, browser=args.browser) as downloader:
            for index, paper in enumerate(papers, start=1):
                title = paper.get("title") or f"Paper {index}"
                print(f"[{index:02d}/{len(papers):02d}] {title}")
                try:
                    result = downloader.download_paper(
                        paper,
                        output_dir,
                        interactive=not args.non_interactive,
                    )
                except StopRequested:
                    stopped = True
                    break
                record = {
                    "index": index - 1,
                    "title": title,
                    "url": paper.get("pdf_url") or paper.get("fallback_url") or "",
                    **result,
                }
                records.append(record)
                if result["status"] == "downloaded":
                    print(f"  OK: {result.get('path', '')}")
                else:
                    print(f"  FAILED: {result.get('reason', '')}")
    except RuntimeError as exc:
        print(f"Downloader error: {exc}", file=sys.stderr)
        return 3

    if stopped:
        for index in range(len(records), len(papers)):
            paper = papers[index]
            records.append(
                {
                    "index": index,
                    "title": paper.get("title") or f"Paper {index + 1}",
                    "url": paper.get("pdf_url") or paper.get("fallback_url") or "",
                    "status": "not_started",
                    "reason": "Task stopped by user",
                    "path": "",
                }
            )

    report_path, failed_path = write_report(output_dir, task, records)
    downloaded = sum(item["status"] == "downloaded" for item in records)
    failed = len(records) - downloaded
    print("\nFinished")
    print(f"Downloaded: {downloaded}")
    print(f"Failed/not started: {failed}")
    print(f"Report: {report_path}")
    if failed_path:
        print(f"Failures: {failed_path}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

