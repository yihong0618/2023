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
    3. add today done
    4. add all list
    5. add show yesterday
    6. add chart?
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
            self.gtd_issue.create_comment(body="Today GTD\n")
            # wait for create
            time.sleep(2)
            self.now_comment = list(self.gtd_issue.get_comments())[-1]
        return body

    def show(self):
        body = self.make_todo_list_body()
        print(body)

    def add(self, todo_string):
        todo_string = "- [ ] " + todo_string + "\r\n"
        body = self.now_comment.body + todo_string + "\r\n"
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
                        new_body_with_done += b + "\r\n"
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

    parser.add_argument(
        "--done",
        dest="done",
        type=int,
        help="which to do to be done",
    )
    parser.add_argument(
        "--undone",
        dest="undone",
        type=int,
        help="which to do to be undone",
    )
    args = args_parser.parse_args()
    gtd = GTD(args.show)
    gtd.show()
    if args.add:
        gtd.add(args.add)
    else:
        if args.done:
            gtd.done_or_undone(args.done, is_done=True)
        if args.undone:
            gtd.done_or_undone(args.undone, is_done=False)


if __name__ == "__main__":
    main()
