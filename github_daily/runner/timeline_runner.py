import os

import pendulum
from datetime import datetime
from github import Github
from rich import print
import openai
from rich.table import Table

from github_daily.config import TIMELINE_LABEL_LIST, REPO_NAME, TIMEZONE, PROMPT
from github_daily.runner.base_runner import BaseRunner


class TimelineRunner(BaseRunner):
    """
    timeline
    - [x] add new
    - [x] list
    - [ ] skip ai answer
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
        self.history = []  # for openai ask with history
        self.with_ai = False

    def show(self):
        comments = self.timeline_issue.get_comments()
        table = Table(title=f"My Timeline {datetime.now().year}")
        table.add_column("Timeline Day", style="cyan", no_wrap=True)
        table.add_column(
            "Timeline Content", justify="left", style="green", overflow="fold"
        )
        if not comments:
            print("No timeline this year for now, go go go to create one")
        for comment in comments:
            comment_day_string = (
                pendulum.instance(comment.created_at)
                .in_timezone(TIMEZONE)
                .to_date_string()
            )
            table.add_row(comment_day_string, comment.body, end_section=True)
        print(table)

    def _make_res(self, timeline_string):
        ms = []
        if self.history:
            first = self.history.pop(0)
            first[0] = PROMPT + first[0]
            ms.append(({"role": "user", "content": first[0]}))
            ms.append({"role": "assistant", "content": first[1]})
        for h in self.history:
            ms.append({"role": "user", "content": h[0]})
            ms.append({"role": "assistant", "content": h[1]})
        ms.append({"role": "user", "content": f"{timeline_string}"})
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=ms,
        )
        res = (
            completion["choices"][0]
            .get("message")
            .get("content")
            .encode("utf8")
            .decode()
        )
        res = res.lstrip("\n").rstrip("\n")
        if res.startswith("> "):
            gpt_res = f"{res}\r\n"
        else:
            gpt_res = f"> {res}\r\n"
        return gpt_res

    def _make_history(self, comment_body):
        body_lines = comment_body.splitlines()
        body_lines = [l for l in body_lines if l]
        for i in range(len(body_lines) - 1):
            query = body_lines[i]
            answer = body_lines[i + 1]
            # trick for time its just for me
            if query[:2].isdigit():
                if answer.startswith("> "):
                    query = query.split(":")[-1]
                    self.history.append([query, answer])

    def add(self, timeline_string, skip_ai=False):
        # do the add
        comments = list(self.timeline_issue.get_comments())
        time_now_string = str(pendulum.now().time())[:8]
        timeline_string = f"{time_now_string}: {timeline_string}"
        if not comments:
            self.timeline_issue.create_comment(body=timeline_string)
        else:
            last_comment = comments[-1]

            if (
                pendulum.today(TIMEZONE).to_date_string()
                == pendulum.instance(last_comment.created_at)
                .in_timezone(TIMEZONE)
                .to_date_string()
            ):
                if self.with_ai:
                    # make history first
                    self._make_history(last_comment.body)
                    gpt_res = self._make_res(timeline_string)
                    timeline_string = (
                        last_comment.body + "\r\n" + timeline_string + "\r\n" + gpt_res
                    )
                else:
                    timeline_string = last_comment.body + "\r\n" + timeline_string
                last_comment.edit(body=timeline_string)
            else:
                # TODO refactor this
                if self.with_ai:
                    completion = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "user", "content": f"{PROMPT}，{timeline_string}"}
                        ],
                    )
                    res = (
                        completion["choices"][0]
                        .get("message")
                        .get("content")
                        .encode("utf8")
                        .decode()
                    )
                    res = res.lstrip("\n").rstrip("\n")
                    timeline_string = timeline_string + "\r\n" + "> " + res + "\r\n"
                self.timeline_issue.create_comment(body=timeline_string)

        print("After add the timeline, now timeline")
        self.show()
