from github_daily.runner.base_runner import BaseRunner

import os
from rich import print
from rich.markdown import Markdown

from github_daily.config import GTD_LABEL_LIST, REPO_NAME, TIMEZONE

from github import Github
import pendulum


class GTDRunner(BaseRunner):
    """
    TODO
    1. - [x] just for today show
    2. - [x] add today add
    3. - [x] add today done
    4. - [ ]add all list
    5. - [ ]add show yesterday
    6. - [ ]add chart?
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
        self.now_comment_gtd_len = 0

    @staticmethod
    def is_the_day(issue_day):
        return (
            pendulum.instance(issue_day).in_timezone(TIMEZONE).to_date_string()
            == pendulum.now(TIMEZONE).to_date_string()
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

        for index, todo in enumerate(body_list[start_index:], 1):
            try:
                front, end = todo.split("]")
                issue_body_with_index += f"{front}] {str(index)}.{end}\r\n"
                # add the todo length
                self.now_comment_gtd_len += 1
            # just pass the wrong format
            except:
                pass
        return issue_body_with_index

    def make_todo_list_body(self):
        if self.show_name not in ["today", "yesterday"]:
            raise Exception("For now only support today or yesterday")
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

    def show(self):
        body = self.make_todo_list_body()
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
        self.show()

    def done_or_undone(self, done_index, is_done=True):
        if done_index > self.now_comment_gtd_len:
            print("your index bigger than all the todo index please check")
            return
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
        print(Markdown(self._add_index_to_todo_body(new_body_with_done)))
        self.now_comment.edit(body=new_body_with_done)
