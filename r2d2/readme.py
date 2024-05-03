import importlib.resources
import os
from pathlib import Path

import keepachangelog
from jinja2 import Template
from tabulate import tabulate

from .pkgs import format_app_versions, get_pkg_data


def build_release_notes(repo1, current_pkgs, previous_pkgs, console, config):
    notes_path = Path.cwd().joinpath(
        f"release-notes-{repo1.next_release_tag.major}-{repo1.next_release_tag.minor}-{repo1.next_release_tag.patch}.md"
    )

    resources_path = importlib.resources.files(__package__)

    template_path = Path.joinpath(resources_path, "templates/release-notes.md")

    md_template = Template(
        template_path.open().read(),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    if Path.exists(notes_path):
        os.remove(notes_path)

    notes = open(notes_path, "w")

    packages_table = []

    upgraded_packages = []

    changelog_diffs = {}

    for name, pkg in current_pkgs.items():
        is_new = previous_pkgs[name] is None

        if not is_new:
            haschanged = pkg["tag"] != previous_pkgs[name]["tag"]
            if not haschanged:
                console.info(f"{name} has not changed")
                # dont include this package in the release notes
                # continue
            else:
                console.warning(
                    f"{name} has changed from {previous_pkgs[name]['tag']} to {pkg['tag']}"
                )
        else:
            console.info(f"{name} is new")
            haschanged = False

        console.spinner.start(f"Building {name}'s package changelog")

        meta = get_pkg_data(pkg)
        if meta is None:
            console.spinner.error(
                console.term.red(
                    f"{name}@{pkg['tag']} Chart not found in repo1.dso.mil"
                )
            )
            continue

        chart, changelog = meta["chart"], meta["changelog"]

        app_versions = format_app_versions(
            chart["annotations"]["bigbang.dev/applicationVersions"]
        )

        # taken from r2-d2.yaml
        if pkg["name"] in config["package_overrides"]:
            pkg["name"] = config["package_overrides"][pkg["name"]]["name"]
            pkg["title"] = config["package_overrides"][pkg["name"]]["title"]

        url = pkg["repo"].replace(".git", "")
        if haschanged and not is_new:
            upgraded_packages.append(
                {
                    **pkg,
                    "url": url,
                    "last_tag": previous_pkgs[name]["tag"],
                }
            )

        row_cols = [
            f"[{pkg['title']}]({url})",
            pkg["type"],
            " ".join(app_versions),
            f"`{pkg['tag']}`",
        ]

        if previous_pkgs[name] is None:
            label = "New"
        elif haschanged:
            label = "Updated"
        else:
            label = ""

        if len(label) > 0:
            row_cols[0] = (
                # f"![{label}: {repo1.next_release_tag}](https://img.shields.io/badge/{label}-{repo1.next_release_tag}-informational?style=flat-square) "
                f"![{label}](https://img.shields.io/badge/{label}-informational?style=flat-square) "
                + row_cols[0]
            )

        # taken from r2-d2.yaml
        pkg_is_beta = name in config["beta_list"]
        if pkg_is_beta:
            row_cols[
                0
            ] += " ![BETA](https://img.shields.io/badge/BETA-purple?style=flat-square)"

        packages_table.append(row_cols)

        # changelog diffs:
        if changelog == None:
            console.spinner.fail(
                console.term.red(
                    f"{name}@{pkg['tag']} Failed to parse CHANGELOG, manual intervention required."
                )
            )
            continue
        elif haschanged == True:
            changelog_diff = {}

            for k, v in changelog.items():
                if k == previous_pkgs[name]["tag"]:
                    break
                changelog_diff[k] = v

            dirty_diff = keepachangelog.from_dict(changelog_diff)
            dirty_diff = dirty_diff.replace(" - 1970-01-01", "")
            clean_diff = "\n".join(dirty_diff.split("\n")[6:-2])
            changelog_diffs[pkg["title"]] = clean_diff

        console.spinner.stop()

    notes.write(
        md_template.render(
            packages_table=tabulate(
                packages_table,
                headers=["Package", "Type", "Package Version", "BB Version"],
                tablefmt="github",
            ),
            last_release=repo1.last_release_tag,
            next_release_tag=repo1.next_release_tag,
            mr_changes=repo1.get_completed_mrs(),
            changelog_diffs=changelog_diffs,
            upgraded_packages=upgraded_packages,
        )
    )

    notes.close()

    console.success("Release notes written to ./build/")
