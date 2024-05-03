import importlib.resources
import json
import os
import shutil
from pathlib import Path
from shutil import copy2

import inquirer
from pyfiglet import Figlet
from ruamel.yaml import YAML

from .console import Console
from .gitlab import BigBangRepo1
from .readme import build_release_notes
from .repo import BigBangRepo

setup_questions = [
    inquirer.Password(
        "repo1_token",
        message="Enter your personal access token for repo1.dso.mil",
        validate=lambda _, x: len(x) > 0 and x.startswith("repo1"),
    ),
    inquirer.Text(
        "bb_path",
        message="Enter the relative path to your cloned Big Bang repo",
        default="../bigbang",
    ),
    # {
    #     "type": "list",
    #     "name": "release_type",
    #     "message": "What type of release?",
    #     "choices": [
    #         "major",
    #         "minor",
    #         "patch",
    #     ],
    #     "default": "minor",
    # },
]

config_questions = [
    inquirer.Checkbox(
        "steps",
        message="What would you like to do?",
        choices=[
            "Check last release SHAs",
            "Create release branch",
            "Build release notes",
            "Upgrade version references",
        ],
    ),
]


def cli():
    console = Console()
    t = Figlet(font="slant")
    print(console.term.green_bold(t.renderText("R2-D2")))

    is_first_run = not Path.home().joinpath(".r2d2/config.yaml").exists()

    resources_path = importlib.resources.files(__package__)

    base_config_path = Path.joinpath(resources_path, "templates/config.yaml")
    config_path = Path.home().joinpath(".r2d2/config.yaml")

    if is_first_run:
        console.info("This is your first run. Let's get you set up.")
        os.makedirs(Path.home().joinpath(".r2d2"), exist_ok=True)
        copy2(base_config_path, config_path)

        config_from_yaml = YAML().load(base_config_path.open())
        setup = console.prompt(setup_questions)
        if "repo1_token" not in setup or "bb_path" not in setup:
            shutil.rmtree(Path.home().joinpath(".r2d2"))
            exit()
        config_from_yaml["repo1_token"] = setup["repo1_token"]
        config_from_yaml["bb_path"] = setup["bb_path"]
        with config_path.open("w") as f:
            YAML().dump(config_from_yaml, f)
    else:
        config_from_yaml = YAML().load(config_path.open())
        console.info("Using cached creds+config from ~/.r2d2/config.yaml")

    if config_from_yaml["interactive"] is True:
        config = {
            **console.prompt(config_questions),
            **config_from_yaml,
        }
    else:
        config = config_from_yaml

    if len(config["steps"]) == 0:
        console.error("You must use spacebar to select/deselect the steps you want to run.")
        console.error("Then hit ENTER to run the selected steps.")
        exit()

    repo1 = BigBangRepo1(
        token=config["repo1_token"],
        release_type=config["release_type"],
    )

    repo = BigBangRepo(bb_path=config["bb_path"])

    console.is_interactive = config["interactive"]
    console.log_level = config["log_level"]

    console.spinner.start("Authenticating with Repo1")
    is_authenticated = repo1.authenticate()
    if is_authenticated is False:
        console.spinner.fail(console.term.red("Auth failed, invalid token"))
        exit(1)
    console.spinner.succeed(console.term.green("Authenticated"))

    if console.log_level == "debug":
        console.spinner.start("Calculating last and next release tags")
        repo1.calculate_release_tags()
        console.spinner.succeed(
            console.term.green("Calculated last and next release tags")
        )
        console.log(":point_right: Last release branch: " + repo1.last_release_tag_x)
        console.log(
            ":point_right: Last release tag: "
            + json.dumps(repo1.last_release_tag.to_dict())
        )
        console.log(":point_right: Next release branch: " + repo1.next_release_tag_x)
        console.log(
            ":point_right: Next release tag: "
            + json.dumps(repo1.next_release_tag.to_dict())
        )
    else:
        console.spinner.start("Calculating last and next release tags")
        repo1.calculate_release_tags()
        console.spinner.succeed(
            console.term.green("Calculated last and next release tags")
        )

    if "Check last release SHAs" in config["steps"]:
        check = repo1.check_last_release()
        if isinstance(check, Exception):
            console.error(str(check))
        else:
            console.success("Last release SHAs match")
        console.confirm(default=not bool(check))

    if "Create release branch" in config["steps"]:
        branch_exists = repo1.get_branch(f"release-{repo1.next_release_tag_x}")
        if branch_exists:
            repo.pull()
            repo1.set_release_branch(f"release-{repo1.next_release_tag_x}")
        else:
            console.warn(
                f"Creating release branch 'release-{repo1.next_release_tag_x}'"
            )
            are_you_sure = console.confirm()
            if are_you_sure is False:
                console.error("Aborting")
                exit()
            repo.create_branch(f"release-{repo1.next_release_tag_x}")
    else:
        # if we don't select to create a release branch, we still need to calculate it
        if not repo1.get_branch(f"release-{repo1.next_release_tag_x}"):
            console.error(
                f"Release branch 'release-{repo1.next_release_tag_x}' not found."
            )
            exit()
        else:
            repo1.set_release_branch(f"release-{repo1.next_release_tag_x}")

    if "Build release notes" in config["steps"]:
        console.info(f":scroll: Building release notes")
        console.info(f"From BB version: {repo1.last_release_tag}")
        console.info(f"To BB version: {repo1.next_release_tag}")
        console.info(f"Release Branch: {repo1.release_branch}")

        console.spinner.start(f"Checking out {repo1.release_branch}")
        repo.checkout(repo1.release_branch)
        console.spinner.succeed(
            console.term.green(f"Switched to branch {repo1.release_branch}")
        )

        console.success(f"Getting packages from branch {repo1.release_branch}")
        pkgs = repo.get_pkgs()

        console.spinner.start(f"Checking out {str(repo1.last_release_tag)}")
        repo.checkout(str(repo1.last_release_tag))
        console.spinner.succeed(
            console.term.green(f"Switched to branch {str(repo1.last_release_tag)}")
        )

        console.success(f"Getting packages from tag {repo1.last_release_tag}")
        pkgs_last_release = repo.get_pkgs()

        repo.checkout(repo1.release_branch)

        build_release_notes(
            repo1=repo1,
            current_pkgs=pkgs,
            previous_pkgs=pkgs_last_release,
            console=console,
            config=config,
        )

    if "Upgrade version references" in config["steps"]:
        repo.checkout(repo1.release_branch)
        console.spinner.start("Upgrading version refs on local Big Bang repo")
        repo.update_base_gitrepository_yaml(str(repo1.next_release_tag))
        repo.update_chart_release_version(str(repo1.next_release_tag))
        repo.run_helm_docs()
        console.spinner.succeed(
            console.term.green("Version refs upgraded on local Big Bang repo")
        )
        console.warning(
            "ALERT: Please review the changes to your local Big Bang and commit if correct"
        )
        console.log(
            f"""
{console.term.gray('$')} {console.term.yellow('cd ' + config["bb_path"])}
{console.term.gray('$')} {console.term.yellow('git status')}

{console.term.gray('$')} {console.term.yellow('yq ".spec.ref.tag" base/gitrepository.yaml')}
# Verify the above prints {console.term.blue(str(repo1.next_release_tag))}

{console.term.gray('$')} {console.term.yellow('yq ".version" chart/Chart.yaml')}
# Verify the above prints {console.term.blue(str(repo1.next_release_tag))}

Check the Big Bang MRs in the release notes 
to see if any packages have enabled mTLS strict 
since last release, and update {console.term.blue('./Packages.md')} accordingly.
"""
        )


if __name__ == "__main__":
    cli()
