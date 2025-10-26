# Apache Jira Scraper

A modular Python application for scraping Apache Jira issues for publically listed projects such as HADOOP, SPARK, KAFKA etc. and converting them into JSONL format suitable for LLM training.

## Project Structure

The project has been organized into modular components:

```
web_scraper/
├── scraper.py        # Contains the main entry point and scraper logic
├── config.py         # Contains default constant values
├── models.py         # Data models for Jira issues, currently only has one class,
├                       but later more classes can be added based on requirements
├── utils.py          # Utility functions for text processing
├── requirements.txt  # Contains the required dependencies and versions for the same
└── README.md         # readme containing setup and how to run instructions
```

## Setup instructions

### Create the virtual environment
- create the virtual environment using the command 
```bash
python -m venv venv
```

### Activate the virtual environment
- activate the virtual environment using the command 
```bash
venv\Scripts\activate
```

### Install the required dependecies
- install the required dependecies using the command from requirements.txt file
```bash
pip install -r requirements.txt
```

### [Optional] Change the default values in config.py if required. Currently the values are
```bash
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
```


## Usage

- The command line command can be used as
```bash
python scraper.py --projects project1 project2 ... --output output_path
```

### Sample command

```bash
python scraper.py --projects HADOOP SPARK KAFKA --output output.jsonl
```

### Output
- Once the command is run a output folder containing output files will be created in the root folder. The folder will contain.
   - jira_checkpoint.json -> A file containing the index of the last extracted issue for each project.
   - Indivdual jira issues files for each project.
   - A combined issues files containing the issues for all the projects.

### Command-line Arguments

- `--projects` / `-p`: Project keys to scrape (required)
- `--output` / `-o`: Output JSONL file path (default: `apache_jira_issues.jsonl`)
- `--checkpoint` / `-c`: Checkpoint file path (default: `jira_checkpoint.json`)
- `--max-results` / `-m`: Results per page (default: 50)

## Architecture Overview

- The project is divided into multiple modules namely scraper containing the scraping logic, utils containing utility functions such as to strip_html to clean the response and return plain text and models to store the class format in which the data is supposed to be strored in json lines file.

## Design Reasoning and Benefits of Modular Structure

1. **Separation of Concerns**: Each module has a single, well-defined responsibility
2. **Maintainability**: Easier to locate and modify specific functionality
3. **Testability**: Individual modules can be tested independently
4. **Reusability**: Utility functions can be imported in other projects
5. **Scalability**: Easy to add new features without cluttering existing code

## Edge Cases handled

1. **Status code 429**: Too many requests, To handle this scenario the waiting time is extracted from the response header or 60 seconds is choosen as a default value in case the header is not present.
2. **Status code 5XX**: To handle the same the request is retried after 5 second, in case the issue is temporal and the request is served after 5 seconds.
3. **Any other status code**: In any other case, the process is failed for the current project and the execution proceeds normally for the other projects. The user can retry to get more issues by running the command again in the terminal.

## Optimisation
1. For a projects which has a lot of issue tickets, the code is optimised to stop after fetching first 10K issues only. This optimiosation is done so that the program does not run forever and the user can see what the actual output looks like.
2. For each project the issues extracted are stored in different individual files so the user can bifurcate the various issues scraped for different projects.
3. The checkpoint file for the project is updated after each page is exracted and if there is a failure during the extraction of any particular page the checkpoint file make sure that next time the issues are only extracted after that paricular checkpoint.

# Future Improvements
- First support for multithreading using asyncio can be added in the system so that issues for the projects are extracted asynchronously and parallely as this is a io bound process where after firing the HTTP request the CPU is waiting for the response and is blocked until it gets a response back from the apache server.
- Second, the jira checkpoint file can be broken down into individual checkpoint files for each project. So that the race condition does not occur when multiple threads are trying to modify the same resource\
