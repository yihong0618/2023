# 2023.02.07 for now just for me, that make a cli eaisy to use 2023
# lets call it gh2023
# use Python for now maybe Rust in the future
import argparse
import time
import os
from rich import print
from rich.markdown import Markdown

# for dev
if __name__ == "__main__":
    from config import GTD_LABEL_LIST, REPO_NAME, TIMEZONE
else:
    from .config import GTD_LABEL_LIST, REPO_NAME, TIMEZONE

from github import Github
import pendulum


class GTD:
    """
    TODO
    1. just for today show
    2. add today add
    4. add today done
    """

    def __init__(self, show_name):
        self.show_name = show_name
        self.g = Github(os.getenv("GITHUB_TOKEN"))
        # only for the latest one
        gtd_issues = list(self.g.get_repo(REPO_NAME).get_issues(labels=GTD_LABEL_LIST))
        if not gtd_issues:
            raise Exception("No gtd issue please create one")
        self.gtd_issue = gtd_issues[0]
        self.now_comment = None

    @staticmethod
    def is_the_day(issue_day):
        return (
            pendulum.instance(issue_day).in_timezone(TIMEZONE).to_date_string()
            == pendulum.now(TIMEZONE).to_date_string()
        )

    def make_todo_list_body(self):
        if self.show_name not in ["today", "yesterday"]:
            raise Exception("For now only support today or yesterday")
        body = ""
        for issue_comment in self.gtd_issue.get_comments():
            if self.is_the_day(issue_comment.created_at):
                body = Markdown(issue_comment.body)
                self.now_comment = issue_comment
                break
        else:
            self.gtd_issue.create_comment(body="Today GTD\n")
            # wait for create
            time.sleep(3)
            self.now_comment = list(self.gtd_issue.get_comments())[-1]
        return body

    def show(self):
        body = self.make_todo_list_body()
        print(body)

    def add(self, todo_string):
        todo_string = "- [ ] " + todo_string + "\r\n"
        body = self.now_comment.body + todo_string + "\r\n"
        self.now_comment.edit(body=body)
        print("Now TODO list after add")
        self.show()


def main():
    args_parser = argparse.ArgumentParser()
    subparser = args_parser.add_subparsers()
    parser = subparser.add_parser(name="gtd")
    parser.set_defaults(type="gtd")

    parser.add_argument(
        "--show",
        dest="show",
        type=str,
        default="today",
        choices=["today", "yesterday"],
        help="show today todo list",
    )
    parser.add_argument(
        "--add",
        dest="add",
        type=str,
        help="to do stringto add",
    )

    args = args_parser.parse_args()
    gtd = GTD(args.show)
    gtd.show()
    if args.add:
        gtd.add(args.add)


if __name__ == "__main__":
    main()
