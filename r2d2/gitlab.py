import gitlab

# using semver==2.13.0
import semver


class BigBangRepo1:
    def __init__(self, token, release_type):
        self.token = token
        self.release_type = release_type
        self.url = "https://repo1.dso.mil/"
        self.bb_id = 2872
        self.gl = gitlab.Gitlab(self.url, private_token=self.token)

    def authenticate(self):
        try:
            self.repo1 = self.gl.projects.get(self.bb_id)
            return True
        except gitlab.exceptions.GitlabAuthenticationError:
            return False

    def get_completed_mrs(self):
        return self.repo1.mergerequests.list(
            state="merged",
            order_by="updated_at",
            milestone=str(self.next_release_tag),
            all=True,
        )

    def calculate_release_tags(self):
        all_releases = list(
            filter(
                lambda tag: "rc" not in tag.tag_name,
                self.repo1.releases.list(all=True),
            )
        )

        # calculate last release tag + last release tag x
        self.last_release = all_releases[0]
        self.last_release_tag = self.last_release.tag_name

        self.last_release_tag = semver.VersionInfo.parse(self.last_release_tag)
        if self.last_release_tag.patch == 0:
            # was a minor release
            self.last_release_tag_x = (
                ".".join(str(self.last_release_tag).split(".")[:2]) + ".x"
            )
        elif self.last_release_tag.minor == 0:
            # was a major release
            self.last_release_tag_x = str(self.last_release_tag).split(".")[0] + ".x.x"
        else:
            # was a patch release
            self.last_release_tag_x = str(self.last_release_tag)

        # calculate next release tag + next release tag x
        next_release_tag = ""

        if self.release_type == "major":
            next_release_tag = self.last_release_tag.bump_major()
            self.next_release_tag_x = str(next_release_tag).split(".")[0] + ".x.x"
        elif self.release_type == "minor":
            next_release_tag = self.last_release_tag.bump_minor()
            self.next_release_tag_x = (
                ".".join(str(next_release_tag).split(".")[:2]) + ".x"
            )
        elif self.release_type == "patch":
            next_release_tag = self.last_release_tag.bump_patch()
            self.next_release_tag_x = str(next_release_tag)
            # idk what to do here lol ^^

        self.next_release_tag = next_release_tag

    def get_branch(self, branch_name):
        try:
            branch = self.repo1.branches.get(branch_name)
            return branch
        except gitlab.exceptions.GitlabGetError:
            return False

    def set_release_branch(self, name):
        self.release_branch = name

    def create_branch(self, branch_name, ref="master"):
        try:
            release_branch = self.repo1.branches.create(
                {"branch": branch_name, "ref": ref}
            )
        except gitlab.exceptions.GitlabCreateError:
            return Exception("Branch already exists")
        self.release_branch = release_branch.name

    def check_last_release(self):
        try:
            last_release_branch = self.repo1.branches.get(
                f"release-{self.last_release_tag_x}"
            )
        except gitlab.exceptions.GitlabGetError:
            return Exception("No release branch found for {self.last_release_tag_x}")

        last_release_commit = self.last_release.commit["short_id"]
        last_release_author = self.last_release.commit["author_name"]

        last_release_branch_hash = last_release_branch.commit["short_id"]

        if last_release_branch_hash != last_release_commit:
            return Exception(
                f"""Tag {self.last_release_tag} release hash != {last_release_branch.name} branch hash
:point_right: Get in contact w/ the previous RE --> {last_release_author}
"""
            )
        return True
