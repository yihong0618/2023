import os

import pendulum
from datetime import datetime
from github import Github
from rich import print
from rich.table import Table

from github_daily.config import TIMELINE_LABEL_LIST, REPO_NAME, TIMEZONE
from github_daily.runner.base_runner import BaseRunner


class TimelineRunner(BaseRunner):
    """
    timeline 
    - [x] add new 
    - [x] list
    """

    def __init__(self):
        super().__init__()
        self.g = Github(os.getenv("GITHUB_TOKEN"))
        # only for the latest one
        timeline_issues = list(
            self.g.get_repo(REPO_NAME).get_issues(labels=TIMELINE_LABEL_LIST)
        )
        if not timeline_issues:
            raise Exception("No idea issue please create one")
        self.timeline_issue = timeline_issues[0]
        self.show_day = "all"

    def show(self):
        comments = self.timeline_issue.get_comments()
        table = Table(title=f"My READ {datetime.now().year}")
        table.add_column("Timeline Day", style="cyan", no_wrap=True)
        table.add_column("Timeline Content", justify="left", style="green")
        if not comments:
            print("No timeline this year for now, go go go to create one")
        for comment in comments:
            comment_day_string = (
                pendulum.instance(comment.created_at)
                .in_timezone(TIMEZONE)
                .to_date_string()
            )
            table.add_row(comment_day_string, comment.body)
        print(table)

    def add(self, timeline_string):
        # do the add
        comments = list(self.timeline_issue.get_comments())
        if not comments:
            self.timeline_issue.create_comment(body=timeline_string)
        else:
            last_comment = comments[-1]

            if pendulum.today(TIMEZONE).to_date_string() == pendulum.instance(last_comment.created_at).in_timezone(TIMEZONE).to_date_string():
                timeline_string = last_comment.body + "\r\n" + timeline_string
                last_comment.edit(body=timeline_string)         
            else:
                self.timeline_issue.create_comment(body=timeline_string)
        
        print("After add the timeline, now timeline")
        self.show()