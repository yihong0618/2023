import os

import pendulum
from github import Github
from rich import print
from rich.markdown import Markdown

from github_daily.config import GTD_LABEL_LIST, REPO_NAME, TIMEZONE
from github_daily.runner.base_runner import BaseRunner
from github_daily.runner.utils import day_to_pendulum


class GTDRunner(BaseRunner):
    """
    TODO
    1. - [x] just for today show
    2. - [x] add today add
    3. - [x] add today done
    4. - [x] add all list
    5. - [x] add show yesterday
    6. - [ ] add chart?
    """

    def __init__(self):
        # default show day is today
        self.show_day = "today"
        self.g = Github(os.getenv("GITHUB_TOKEN"))
        # only for the latest one
        gtd_issues = list(self.g.get_repo(REPO_NAME).get_issues(labels=GTD_LABEL_LIST))
        if not gtd_issues:
            raise Exception("No gtd issue please create one")
        self.gtd_issue = gtd_issues[0]
        self.now_comment = None
        self.now_comment_gtd_len = 0

    def is_the_day(self, issue_day):
        day = day_to_pendulum(self.show_day)
        return (
            pendulum.instance(issue_day).in_timezone(TIMEZONE).to_date_string()
            == day.to_date_string()
        )

    def _add_index_to_todo_body(self, body):
        body_list = body.splitlines()
        issue_body_with_index = ""
        start_index = 0
        for b in body_list:
            if b.startswith("- [ ]") or b.startswith("- [x]"):
                break
            else:
                issue_body_with_index += b + "\r\n"
                start_index += 1

        for _, todo in enumerate(body_list[start_index:], 1):
            try:
                front, end = todo.split("]")
                self.now_comment_gtd_len += 1
                issue_body_with_index += (
                    f"{front}] {str(self.now_comment_gtd_len)}.{end}\r\n"
                )
                # add the todo length
            # just pass the wrong format
            except:
                pass
        return issue_body_with_index

    def make_todo_list_body(self):
        if self.show_day not in ["today", "yesterday"]:
            raise Exception("For now only support today or yesterday or all")
        body = ""
        for issue_comment in self.gtd_issue.get_comments():
            if self.is_the_day(issue_comment.created_at):
                body = Markdown(
                    "---\r\n"
                    + self._add_index_to_todo_body(issue_comment.body)
                    + "\r\n---\r\n"
                )
                self.now_comment = issue_comment
                break
        else:
            body = "Today GTD: "
            self.now_comment = self.gtd_issue.create_comment(body=body)
        return body

    def make_todo_list_body_all(self):
        if self.show_day != "all":
            raise Exception("For now only support all")
        body = ""
        for issue_comment in self.gtd_issue.get_comments():
            body += issue_comment.body
        body = Markdown("---\r\n" + self._add_index_to_todo_body(body) + "\r\n---\r\n")
        return body

    def show(self):
        if self.show_day in ["today", "yesterday"]:
            body = self.make_todo_list_body()
        else:
            body = self.make_todo_list_body_all()
        print(body)

    def add(self, todo_string):
        todo_string = "- [ ] " + todo_string
        comment_body = self.now_comment.body
        if comment_body:
            # new line in GitHub is \r\n
            if not (comment_body[-1] == "\n" and comment_body[-2] == "\r"):
                comment_body = comment_body + "\r\n"
        body = comment_body + todo_string
        self.now_comment.edit(body=body)
        print("Now TODO list after added")
        self.now_comment_gtd_len = 0
        self.show()

    def done_or_undone(self, done_index, is_done=True):
        if done_index > self.now_comment_gtd_len:
            print("your index bigger than all the todo index please check")
            return
        if self.show_day == "all":
            raise Exception("do not support all for done or undone")
        index = 0
        new_body_with_done = ""
        starts_str_list = ["- [ ]", "- [x]"]
        starts_str = starts_str_list[is_done]
        for b in self.now_comment.body.splitlines():
            if b.startswith("- [ ]") or b.startswith("- [x]"):
                index += 1
                if index == done_index:
                    if b.startswith(starts_str):
                        print(f"This is already {'done' if is_done else 'undone'}")
                        return
                        # Do nothing
                    else:
                        # tricky for only two elements list
                        b = b.replace(
                            starts_str_list[not is_done], starts_str_list[is_done]
                        )
                        new_body_with_done += b + "\r\n"
                else:
                    new_body_with_done += b + "\r\n"

            else:
                new_body_with_done += b + "\r\n"
        self.now_comment_gtd_len = 0
        print(Markdown(self._add_index_to_todo_body(new_body_with_done)))
        self.now_comment.edit(body=new_body_with_done)
