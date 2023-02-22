import os

import pendulum
from datetime import datetime
from github import Github
from rich import print
from rich.table import Table

from github_daily.config import READ_LABEL_LIST, REPO_NAME, TIMEZONE
from github_daily.runner.base_runner import BaseRunner


class ReadRunner(BaseRunner):
    """
    books
    - [x] add book
    - [x] list
    """

    def __init__(self):
        super().__init__()
        self.g = Github(os.getenv("GITHUB_TOKEN"))
        # only for the latest one
        read_issues = list(
            self.g.get_repo(REPO_NAME).get_issues(labels=READ_LABEL_LIST)
        )
        if not read_issues:
            raise Exception("No idea issue please create one")
        self.read_issue = read_issues[0]
        self.show_day = "all"

    def show(self):
        comments = self.read_issue.get_comments()
        table = Table(title=f"My READ {datetime.now().year}")
        table.add_column("Read Day", style="cyan", no_wrap=True)
        table.add_column("Book Title", justify="left", style="green")
        table.add_column("Read Content", justify="left", style="green")
        if not comments:
            print("No read this year for now, go go go to create one")
        for comment in comments:
            comment_day_string = (
                pendulum.instance(comment.created_at)
                .in_timezone(TIMEZONE)
                .to_date_string()
            )
            c = comment.body.splitlines()
            book_title = c[0]
            read_content = "".join(c[1:])
            table.add_row(comment_day_string, book_title, read_content)
        print(table)

    def add(self, read_string):
        # do the add
        book_string = ""
        r = read_string.split()
        book_name = r[0]
        if not book_name.startswith("《"):
            book_name = "《" + book_name + "》"
        book_content = "".join(r[1:])
        book_string = book_name + "\r\n" + "\r\n" + book_content
        self.read_issue.create_comment(body=book_string)
        print("After add the idea, now ideas")
        self.show()
