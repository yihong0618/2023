import os

import pendulum
from github import Github
from rich import print
from rich.table import Table

from github_daily.config import IDEA_LABEL_LIST, REPO_NAME, TIMEZONE
from github_daily.runner.base_runner import BaseRunner


class IdeaRunner(BaseRunner):
    """
    TODO
    1. - [x] show all ideas -> table
    2. - [x] get ideas
    3. - [ ] random idea
    4. - [x] add idea
    """

    def __init__(self):
        super().__init__()
        self.g = Github(os.getenv("GITHUB_TOKEN"))
        # only for the latest one
        idea_issues = list(
            self.g.get_repo(REPO_NAME).get_issues(labels=IDEA_LABEL_LIST)
        )
        if not idea_issues:
            raise Exception("No idea issue please create one")
        self.idea_issue = idea_issues[0]
        self.show_day = "all"

    def show(self):
        comments = self.idea_issue.get_comments()
        table = Table(title="My ideas")
        table.add_column("Idea Time", style="cyan", no_wrap=True)
        table.add_column("Idea Content", justify="middle", style="green")
        if not comments:
            print("No idea this year for now, go go go to create one")
        for comment in comments:
            comment_day_string = (
                pendulum.instance(comment.created_at)
                .in_timezone(TIMEZONE)
                .to_date_string()
            )
            table.add_row(comment_day_string, comment.body.strip())
        print(table)

    def add(self, idea_string):
        # do the add
        self.idea_issue.create_comment(body=idea_string)
        print("After add the idea, now ideas")
        self.show()
