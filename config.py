# Jira API configuration
JIRA_BASE = "https://issues.apache.org/jira"
SEARCH_API = f"{JIRA_BASE}/rest/api/2/search"

# Default values
DEFAULT_MAX_RESULTS = 50
TIMEOUT = 30
CHECKPOINT_DEFAULT = "output/jira_checkpoint.json"
OUTPUT_DEFAULT = "output/apache_jira_issues"

# Logging configuration
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
LOG_LEVEL = "INFO"
