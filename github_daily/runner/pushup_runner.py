import os
from collections import defaultdict

import pendulum
from datetime import datetime
from github import Github
from rich import print
from rich.table import Table

from github_daily.config import PUSHUP_LABEL_LIST, REPO_NAME, TIMEZONE
from github_daily.runner.base_runner import BaseRunner


class PushupRunner(BaseRunner):
    """
    books
    - [x] add book
    - [x] list
    """

    def __init__(self):
        super().__init__()
        self.g = Github(os.getenv("GITHUB_TOKEN"))
        # only for the latest one
        pushup_issues = list(
            self.g.get_repo(REPO_NAME).get_issues(labels=PUSHUP_LABEL_LIST)
        )
        if not pushup_issues:
            raise Exception("No idea issue please create one")
        self.pushup_issue = pushup_issues[0]
        self.show_day = "all"

    def show(self):
        comments = self.pushup_issue.get_comments()
        table = Table(title=f"My Pushups {datetime.now().year}")
        table.add_column("Pushup Day", style="cyan", no_wrap=True)
        table.add_column("Count", justify="left", style="green")
        pushups_dict = defaultdict(int)
        if not comments:
            print("No pushups this year for now, go go go to create one")
        for comment in comments:
            comment_day_string = (
                pendulum.instance(comment.created_at)
                .in_timezone(TIMEZONE)
                .to_date_string()
            )
            c = comment.body.splitlines()
            pushup_count = c[0]
            pushups_dict[comment_day_string] += int(pushup_count)
        for k, v in pushups_dict.items():
            table.add_row(k, str(v))
        print(table)

    def add(self, pushup_string):
        # do the add
        r = pushup_string.split()
        comment = ""
        if len(r) == 1:
            count = r[0][0]
            if len(r[0]) > 1:
                comment = "\r\n" + "".join(r[1:])
        else:
            count = r[0]
            comment = "\r\n" + "".join(r[1:])
        try:
            int(count)
        except:
            raise Exception("first must be a number")
            return
        pushup_string = f"{count}{comment}"
        self.pushup_issue.create_comment(body=pushup_string)
        print("After add the new pushup, now pushups")
        self.show()
