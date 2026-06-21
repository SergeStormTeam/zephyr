# Zephyr ![Static Badge](https://img.shields.io/badge/weather-%23b16ded?style=flat&logo=github&logoColor=black&labelColor=0%2C0%2C0&link=https%3A%2F%2Fgithub.com%2FweatherGod3218%2F)

## What is Zephyr?

Zephyr is the SERGE team's second mobile deployment probe. Being the successor to the Wisconsin Mobile Storm Probe, Zephyr aims to end all of the issues that bloomed with the original.
Some of the notable editions is the new all metal design, leading to an extremely more weather resilient probe. It also features the addition of a SEN-15901 Weather Station for Wind Speed, Wind Direction and Precipitation
The data from this probe is then sent to SERGE's servers on the fly in order to backup the data collected.

## Local Development

### NOTE: MAKE SURE TO USE `uv add` IN THIS PROJECT TO KEEP `pyproject.toml` and `uv.lock` UPDATED!
## UV Setup

Install UV on your system if not already on it. If you already have it installed, you can skip down to the Project Setup page

UV is a blazingly fast python package manager written in Rust. The Jumpstart project uses UV for speed and simplicity. Run the linked install command for your operating system

__Linux and macOS__
```
    curl -LsSf https://astral.sh/uv/install.sh | sh
```

__Windows (Powershell)__
```
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## UV Commands Useful For this Project

__uv sync__: UV sync serves to replace pip install -r requirements.txt. This command syncs your virtual environment to match the `pyproject.toml` file. By default, it will only copy the default dependencies for the project (found in dependencies)

__uv sync --group $GROUP__: UV sync with the added group flag will ALSO install all dependencies found in that group ALONG with the default dependencies.

__uv sync --frozen__: When reading the UV Sync, it reads ONLY the `uv.lock` file, and does not attempt to make any modifications, and failing instead. This is incredibly useful for reproducibility, which is why its used in the docker file.

__uv sync --all-groups__: UV sync, along with installing dependencies of every group

__uv add $PACKAGE__: UV serves to replace pip install $PACKAGE. It installs the most recent version of the inserted package, and adds it to the projects default dependencies

__uv add --group $GROUP $PACKAGE__: Same as UV add, but adds the package to the group instead of the default project dependencies.


## Project Setup
1. Run: `uv venv .venv --python 3.14.5`
2. Activate the virtual environment
    * Bash: `source .venv/bin/activate`
    * Fish: `source .venv/bin/activate.fish`
    * Windows: `.venv\Scripts\activate`
    * Other: Good luck!
3. Run: `uv sync --group dev --group tests`
4. Run: `pre-commit install`
5. You're all set!

## Running the Application

This app is containerized through a docker file.

1. Build the docker file
```
    docker build -t zephyr .
```
2. Run the newly built docker on port 8000
```
    docker run -p 8000:8000 zephyr
```

## Docker Compose

the zephyr application also has support for Docker Compose, a extended version of docker that simplifies the steps.

(This is a really cool thing! If you use docker often, check it out!)
```
    docker compose up --build
```

sudo apt update && sudo apt install -y liblgpio-dev

### Testing

We're using the pytest framework to create tests. A good minimum coverage requirement is about <=90%.

To run the tests just run: `uv run pytest`

`coverage.xml` and `htmlcov` should be generated. `coverage.xml` is used for Sonarqube, while `htmlcov` is a local html view into code coverage. The easiest way to view the coverage site is to enter the directory and run: `python -m http.server` and visit the site!
