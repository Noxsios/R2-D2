# R2-D2 - Robotic Release Documentation Delivery

## Installing

Python 3.9+ is a prereq.

```shell
# create a venv if needed
python3 -m venv venv
source venv/bin/activate

# install from git
python3 -m pip install git+https://github.com/noxsios/r2-d2.git
```

## Usage

Run in interactive CLI mode:

```shell
r2d2
```

Run in noninteractive CLI mode w/ config from [`~/.r2d2/config.yaml`](r2d2/templates/config.yaml):

```shell
yq -i '.interactive = false' ~/.r2d2/config.yaml
# replace below w/ your Repo1 token
yq -i '.repo1_token = "<token>"' ~/.r2d2/config.yaml
# replace below w/ relative path to your local cloned bigbang repo
yq -i '.bb_path = "<path>"' ~/.r2d2/config.yaml
# steps you want to run, ex. "Check last release SHAs", "Create release branch"
yq -i '.steps = ["<step1>", "<step2>", "<step3>"]' ~/.r2d2/config.yaml

# run it
r2d2
```

## Developing

This project requires the `poetry` python package to be installed globally.  For developing on Windows, I recommend using the [`Open Folder in a Container...`](https://code.visualstudio.com/docs/remote/containers) feature of VS Code and opening in a Python 3.9+ container.

```shell
pip install poetry
```

After installation, you can run the following commands to install the project dependencies:

```shell
poetry config virtualenvs.in-project true
# ^ this is so that vscode can find the venv
poetry install

# run w/
poetry run r2d2
```