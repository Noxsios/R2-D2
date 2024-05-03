import os
from pathlib import Path

import docker
import git
from ruamel.yaml import YAML

yaml = YAML(typ="rt")
# indent 2 spaces extra on lists
yaml.indent(mapping=2, sequence=4, offset=2)
# prevent opinionated line wrapping
yaml.width = 1000


class BigBangRepo:
    def __init__(self, bb_path):
        self.bb_path = bb_path
        self.abs_bb_path = Path.cwd().joinpath(bb_path)
        self.repo = git.Repo(self.abs_bb_path)

        if self.repo.is_dirty():
            print(
                "Your local Big Bang repo has pending changes, please commit or stash them"
            )
            exit()
        else:
            self.repo.git.pull()
            self.repo.git.checkout("master")

    def pull(self):
        self.repo.git.pull()

    def checkout(self, ref):
        if self.repo.is_dirty():
            print(
                "Your local Big Bang repo has pending changes, please commit or stash them"
            )
            return
        self.repo.git.checkout(ref)

    def get_pkgs(self):
        """
        Use the values.yaml located in bigbang/chart/values.yaml to get the pkgs and their versions
        """
        pkgs = {}
        values_yaml = open(self.bb_path + "/chart/values.yaml", "r")
        values = yaml.load(values_yaml)

        # core
        for _, v in values.items():
            if isinstance(v, dict) and "git" in v:
                pkg = v["git"]
                pkg["name"] = pkg["repo"].split("/")[-1].split(".")[0]
                pkg["title"] = pkg["name"].replace("-", " ").title()
                pkg.pop("path", None)
                pkg["type"] = "Core"
                pkgs[pkg["name"]] = pkg
        # addons
        for _, v in values["addons"].items():
            if isinstance(v, dict) and "git" in v:
                pkg = v["git"]
                pkg["name"] = pkg["repo"].split("/")[-1].split(".")[0]
                pkg["title"] = pkg["name"].replace("-", " ").title()
                pkg.pop("path", None)
                pkg["type"] = "Addon"
                pkgs[pkg["name"]] = pkg

        return pkgs

    def run_helm_docs(self):
        client = docker.from_env()
        readme = client.containers.run(
            "jnorwood/helm-docs:v1.5.0",
            "-s file -t .gitlab/README.md.gotmpl --dry-run",
            volumes=[f"{self.abs_bb_path}:/helm-docs"],
        )
        open(self.abs_bb_path + "/README.md", "w").write(readme.decode("utf-8"))

    def update_base_gitrepository_yaml(self, next_release_tag):
        base_gitrepo_yaml_path = Path.joinpath(self.bb_path, "base/gitrepository.yaml")
        with open(base_gitrepo_yaml_path) as base_gitrepo_yaml:
            base_gitrepo = yaml.load(base_gitrepo_yaml)
        with open(base_gitrepo_yaml_path, "w") as base_gitrepo_yaml:
            base_gitrepo["spec"]["ref"]["tag"] = next_release_tag
            yaml.dump(base_gitrepo, base_gitrepo_yaml)

    def update_chart_release_version(self, next_release_tag):
        chart_yaml_path = Path.joinpath(self.bb_path, "chart/Chart.yaml")
        with open(chart_yaml_path) as chart_yaml:
            chart = yaml.load(chart_yaml)
        with open(chart_yaml_path, "w") as chart_yaml:
            chart["version"] = next_release_tag
            yaml.dump(chart, chart_yaml)
