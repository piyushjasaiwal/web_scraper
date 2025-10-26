import datetime
import json
import logging
import os
import time
from typing import Any, Dict, Generator, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import CHECKPOINT_DEFAULT, OUTPUT_DEFAULT, LOG_FORMAT, TIMEOUT, SEARCH_API, DEFAULT_MAX_RESULTS
from models import JiraIssue
from utils import safe_get, strip_html


# Configure logging
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


class JiraScraper:
    """Handles fetching, retrying, and writing issues for given Jira projects."""

    def __init__(self, projects: List[str], output_path: str, checkpoint_path: str, max_results: int):
        self.projects = projects
        self.output_path = output_path
        self.checkpoint_path = checkpoint_path
        self.max_results = max_results
        self.session = self._init_session()
        self.checkpoint = self._load_checkpoint()

    def _init_session(self) -> requests.Session:
        """Initialize HTTP session with retry policy."""
        s = requests.Session()
        retries = Retry(
            total=5, 
            backoff_factor=1, 
            status_forcelist=[429, 500, 502, 503, 504], 
            allowed_methods=["GET"]
        )
        s.mount("https://", HTTPAdapter(max_retries=retries))
        s.mount("http://", HTTPAdapter(max_retries=retries))
        return s

    def _load_checkpoint(self) -> Dict[str, Any]:
        """Load checkpoint to resume from last saved state."""
        if os.path.exists(self.checkpoint_path):
            with open(self.checkpoint_path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        return {}

    def _save_checkpoint(self):
        """Persist current scraping progress to disk."""
        with open(self.checkpoint_path, "w", encoding="utf-8") as fh:
            json.dump(self.checkpoint, fh, indent=2)

    def _request(self, url: str, params: Dict = None) -> Optional[Dict]:
        """Perform GET request with handling for rate limits and server errors."""
        try:
            resp = self.session.get(
                url, 
                params=params,    
                headers={"Accept": "application/json"}, 
                timeout=TIMEOUT
            )
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None

        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", 60))
            logger.warning(f"Rate limited. Waiting {wait}s.")
            time.sleep(wait)
            return self._request(url, params)

        if 500 <= resp.status_code < 600:
            logger.warning(f"Server error {resp.status_code}. Retrying in 5s.")
            time.sleep(5)
            return self._request(url, params)

        if resp.status_code != 200:
            logger.error(f"Unexpected status {resp.status_code}")
            return None

        try:
            return resp.json()
        except ValueError:
            logger.error("Invalid JSON response.")
            return None

    def fetch_issues_for_project(self, project: str) -> Generator[JiraIssue, None, None]:
        """Fetch issues for a given project with pagination and checkpointing."""
        start_at = int(self.checkpoint.get(project, {}).get("startAt", 0))
        more = True
        
        while more:
            params = {
                "jql": f"project={project} ORDER BY created ASC",
                "startAt": start_at,
                "maxResults": self.max_results,
                "fields": "summary,status,priority,reporter,assignee,labels,created,updated,description,comment",
            }
            data = self._request(SEARCH_API, params=params)
            if not data:
                break

            issues = data.get("issues", [])
            total = data.get("total", 0)
            total = min(total, 10000)

            for issue in issues:
                fields = issue.get("fields", {})
                yield JiraIssue(
                    key=issue.get("key"),
                    project=project,
                    title=strip_html(safe_get(fields, "summary")),
                    status=safe_get(fields, "status", "name"),
                    priority=safe_get(fields, "priority", "name"),
                    reporter=safe_get(fields, "reporter", "displayName"),
                    assignee=safe_get(fields, "assignee", "displayName"),
                    labels=safe_get(fields, "labels", default=[]),
                    created=safe_get(fields, "created"),
                    updated=safe_get(fields, "updated"),
                    description=strip_html(safe_get(fields, "description")),
                    comments=[{
                        "author": safe_get(c, "author", "displayName"),
                        "created": safe_get(c, "created"),
                        "body": strip_html(safe_get(c, "body")),
                    } for c in safe_get(fields, "comment", "comments", default=[])],
                )

            start_at += len(issues)
            self.checkpoint.setdefault(project, {})["startAt"] = start_at
            self._save_checkpoint()
            more = start_at < total

    def run(self):
        """Main runner that orchestrates fetching and writing issues to JSONL."""
        total_written = 0
        files = []
        os.makedirs(os.path.dirname(CHECKPOINT_DEFAULT), exist_ok=True)
        for project in self.projects:
            file_output_path = self.output_path+f"_{project}.jsonl"
            files.append(file_output_path)
            written = 0
            with open(file_output_path, "a", encoding="utf-8") as out:
                for issue in self.fetch_issues_for_project(project):
                    out.write(json.dumps(issue.to_corpus(), ensure_ascii=False) + "\n")
                    written += 1
            total_written += written
            logger.info(f"Completed writing {written} issues to {file_output_path}")

        combined_output_path = f"{self.output_path}_combined_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        with open(combined_output_path, "a", encoding="utf-8") as out:
            for file in files:
                with open(file, "r", encoding="utf-8") as f:
                    for line in f:
                        out.write(line)
        logger.info(f"Completed writing {total_written} issues to {combined_output_path}")


# --------------------------- CLI HANDLER ---------------------------

def parse_args():
    """Parse CLI arguments for projects, output path, etc."""
    import argparse
    parser = argparse.ArgumentParser(description="Scrape Apache Jira issues into JSONL format")
    parser.add_argument("--projects", "-p", nargs="+", required=True, help="Project keys, e.g., HADOOP SPARK KAFKA")
    parser.add_argument("--output", "-o", default=OUTPUT_DEFAULT, help="Output JSONL file path")
    parser.add_argument("--checkpoint", "-c", default=CHECKPOINT_DEFAULT, help="Checkpoint file path")
    parser.add_argument("--max-results", "-m", type=int, default=DEFAULT_MAX_RESULTS, help="Results per page")
    return parser.parse_args()


def main():
    """Entry point: parse args and start scraper."""
    args = parse_args()
    scraper = JiraScraper(args.projects, args.output, args.checkpoint, args.max_results)
    scraper.run()


if __name__ == "__main__":
    main()
