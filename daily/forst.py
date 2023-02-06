import argparse
import json
from collections import Counter
from datetime import datetime

import pendulum
import requests
from github import Github

from config import (
    FOREST_CLAENDAR_URL,
    FOREST_ISSUE_NUMBER,
    FOREST_LOGIN_URL,
    FOREST_SUMMARY_HEAD,
    FOREST_SUMMARY_STAT_TEMPLATE,
    FOREST_TAG_URL,
    TIMEZONE,
)


class Forst:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.s = requests.Session()
        self.year = datetime.now().year
        self.user_id = None
        self.plants = []
        self.log_days = []
        self.success_plants_count = 0
        self.is_login = False
        self.issue = None

    def login(self):
        data = {"session": {"email": self.email, "password": self.password}}
        headers = {"Content-Type": "application/json"}
        r = self.s.post(FOREST_LOGIN_URL, headers=headers, data=json.dumps(data))
        if not r.ok:
            raise Exception(f"Someting is wrong to login -- {r.text}")
        self.user_id = r.json()["user_id"]
        self.is_login = True

    def make_plants_data(self):
        date = str(self.year) + "-01-01"
        r = self.s.get(FOREST_CLAENDAR_URL.format(date=date, user_id=self.user_id))
        if not r.ok:
            raise Exception(f"Someting is wrong to get data-- {r.text}")
        self.plants = r.json()["plants"]
        # only count success trees
        self.plants = [i for i in self.plants if i["is_success"]]

    def _get_my_tags(self):
        r = self.s.get(FOREST_TAG_URL.format(user_id=self.user_id))
        if not r.ok:
            raise Exception("Can not get tags")
        tag_list = r.json().get("tags", [])
        tag_dict = {}
        for t in tag_list:
            tag_dict[t["tag_id"]] = t["title"]
        return tag_dict

    def make_year_stats(self):
        if not self.is_login:
            raise Exception("Please login first")
        self.make_plants_data()

    def _make_forest_dict(self, plants):
        if not self.plants:
            self.make_plants_data()
        tags_dict = self._get_my_tags()
        d = Counter()
        for p in plants:
            d[tags_dict[p.get("tag")]] += 1
        return d

    @staticmethod
    def _make_tag_summary_str(tag_summary_dict, unit):
        s = FOREST_SUMMARY_HEAD
        for k, v in tag_summary_dict.most_common():
            s += FOREST_SUMMARY_STAT_TEMPLATE.format(tag=k, times=str(v) + f" {unit}")
        return s

    def make_table_body(self, plants, date_str=""):
        unit = "个"
        body = ""
        tag_summary_dict = self._make_forest_dict(plants)
        for b in self.issue.body.splitlines():
            if b.startswith("|"):
                break
            body += b
        if date_str:
            body = (
                f"{date_str}的 Forst 番茄时间汇总"
                + "\r\n"
                + self._make_tag_summary_str(tag_summary_dict, unit)
            )
        else:
            body = body + "\r\n" + self._make_tag_summary_str(tag_summary_dict, unit)
        return body

    def make_new_table(self, token, repo_name, issue_number=FOREST_ISSUE_NUMBER):
        u = Github(token)
        self.issue = u.get_repo(repo_name).get_issue(issue_number)
        self.make_plants_data()
        plants = self.plants
        body = self.make_table_body(plants)
        self.issue.edit(body=body)

    def make_daily_table(self):
        comments = list(self.issue.get_comments())
        yesterday = pendulum.now(TIMEZONE).subtract(days=1)
        today = pendulum.now(TIMEZONE)
        yesterday_plants = [
            i
            for i in self.plants
            if pendulum.parse(i["start_time"]).in_timezone(TIMEZONE).to_date_string()
            == yesterday.to_date_string()
        ]
        yesterday_body = self.make_table_body(
            yesterday_plants, yesterday.to_date_string()
        )
        today_plants = [
            i
            for i in self.plants
            if pendulum.parse(i["start_time"]).in_timezone(TIMEZONE).to_date_string()
            == today.to_date_string()
        ]
        today_body = self.make_table_body(today_plants, today.to_date_string())
        if not comments:
            # yesterday
            if yesterday_plants:
                self.issue.create_comment(body=yesterday_body)
        else:
            latest_comment = comments[-1]
            latest_day = pendulum.instance(latest_comment.created_at).in_timezone(
                TIMEZONE
            )
            is_today = (latest_day.day == today.day) and (
                latest_day.month == today.month
            )
            is_yesterday = (latest_day.day == yesterday.day) and (
                latest_day.month == yesterday.month
            )
            if is_yesterday:
                latest_comment.edit(body=yesterday_body)
            else:
                if is_today:
                    latest_comment.edit(body=today_body)
                else:
                    self.issue.create_comment(body=today_body)

    def make_forst_daily(self):
        end_date = pendulum.now(TIMEZONE)
        start_date = end_date.start_of("year")
        self.make_year_stats()
        log_days = set(
            [
                pendulum.parse(i["start_time"]).in_timezone(TIMEZONE).to_date_string()
                for i in self.plants
            ]
        )
        self.log_days = sorted(list(log_days))
        is_today_check = False
        if end_date.to_date_string() in self.log_days:
            is_today_check = True
        periods = list(pendulum.period(start_date, end_date.subtract(days=1)))
        periods.sort(reverse=True)

        # if today id done
        streak = 0
        if end_date.to_date_string() in self.log_days:
            streak += 1

        # for else if not break not else
        for p in periods:
            if p.to_date_string() not in self.log_days:
                break
            streak += 1
        # total plants, streak, is_today_check
        return len(self.plants), streak, is_today_check


def get_forst_daily(email, password, github_token, repo_name):
    f = Forst(email, password)
    f.login()
    # also edit the issue body
    f.make_new_table(github_token, repo_name)
    f.make_daily_table()
    return f.make_forst_daily()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("email", help="email")
    parser.add_argument("password", help="password")
    parser.add_argument("github_token", help="github_token")
    parser.add_argument("repo_name", help="repo_name")
    options = parser.parse_args()
    f = Forst(options.email, options.password)
    f.login()
    f.make_new_table(options.github_token, options.repo_name)
    f.make_daily_table()
