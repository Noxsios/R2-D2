import os
from pathlib import Path

import keepachangelog
import requests
from ruamel.yaml import YAML


def get_pkg_data(pkg):
    cache_dir = Path.home().joinpath(f".r2d2/cache/{pkg['name']}_{pkg['tag']}")

    chart_path = cache_dir.joinpath("Chart.yaml")
    changelog_path = cache_dir.joinpath("CHANGELOG.md")
    is_cached = Path.exists(chart_path) and Path.exists(changelog_path)

    if is_cached:
        return {
            "chart": YAML().load(open(chart_path, "r")),
            "changelog": keepachangelog.to_dict(changelog_path),
        }
    else:
        os.makedirs(cache_dir, exist_ok=True)

    # get the chart
    chart_url = f"{pkg['repo'].replace('.git','')}/-/raw/{pkg['tag']}/chart/Chart.yaml"
    chart_res = requests.get(chart_url)
    if chart_res.status_code != 200:
        print(f"\n ERROR: {pkg['name']} {pkg['tag']} Chart not found in repo1.dso.mil")
        return
    chart = chart_res.text
    chart_path.open("w").write(chart)

    # get the changelog
    changelog_url = f"{pkg['repo'].replace('.git','')}/-/raw/{pkg['tag']}/CHANGELOG.md"
    changelog_res = requests.get(changelog_url)
    if changelog_res.status_code != 200:
        print(
            f"\n ERROR: {pkg['name']} {pkg['tag']} CHANGELOG not found in repo1.dso.mil"
        )
        return
    changelog = changelog_res.text
    # some fuckery to make our changelogs actually KAC compliant
    changelog = changelog.replace("\n---", "")
    clean_changelog = []
    for line in changelog.split("\n"):
        if line.startswith("## ") and len(line.split("-")) <= 3:
            line = line.strip() + " - 1970-01-01"
        if line.startswith("#") or line.startswith("-"):
            clean_changelog.append(line)

    changelog = "\n\n".join(clean_changelog)

    changelog_path.open("w").write(changelog)

    return {
        "chart": YAML().load(open(chart_path, "r")),
        "changelog": keepachangelog.to_dict(changelog_path),
    }


def format_app_versions(app_versions):
    app_versions = list(
        filter(
            lambda l: len(l) > 0,
            ([line.replace("- ", "") for line in app_versions.split("\n")]),
        )
    )
    remove_v_prefix = lambda x: x[1:] if x.startswith("v") else x
    if len(app_versions) > 1:
        for idx, app_version in enumerate(app_versions):
            name, version = [item.strip() for item in app_version.split(":")]
            version = remove_v_prefix(version)
            app_versions[idx] = f"{name} `{version}`"
    else:
        _, version = [item.strip() for item in app_versions[0].split(":")]
        version = remove_v_prefix(version)
        app_versions[0] = f"`{version}`"

    return app_versions
