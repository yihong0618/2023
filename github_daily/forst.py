import json
from collections import Counter
from datetime import datetime

import pendulum
import requests
from github import Github

from .config import (
    FOREST_CLAENDAR_URL,
    FOREST_ISSUE_NUMBER,
    FOREST_LOGIN_URL,
    FOREST_SUMMARY_HEAD,
    FOREST_SUMMARY_STAT_TEMPLATE,
    FOREST_TAG_URL,
    TIMEZONE,
)


class Forst:
    def __init__(self, email, password, github_token, repo_name):
        self.email = email
        self.password = password
        self.github_token = github_token
        self.repo_name = repo_name
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
        # login github
        u = Github(self.github_token)
        self.issue = u.get_repo(self.repo_name).get_issue(FOREST_ISSUE_NUMBER)

    def make_plants_data(self):
        if not self.is_login:
            self.login()
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

    # make forst tag like "代码" "日语" as key
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
        if self.issue:
            for b in self.issue.body.splitlines():
                if b.startswith("|"):
                    break
                body += b
        if date_str:
            body = (
                f"{date_str} 的 Forst 番茄时间汇总"
                + "\r\n"
                + self._make_tag_summary_str(tag_summary_dict, unit)
            )
        # if no date str is the issue body --> sunmmary
        else:
            body = body + "\r\n" + self._make_tag_summary_str(tag_summary_dict, unit)
        return body

    def make_year_stats_table(self):
        self.make_plants_data()
        plants = self.plants
        body = self.make_table_body(plants)
        self.issue.edit(body=body)

    def make_plants_body(self, day):
        """
        if there no day we do not need to filter
        TODO refactor here
        """
        if not day:
            return self.make_table_body(self.plants)
        plants = [
            i
            for i in self.plants
            if pendulum.parse(i["start_time"]).in_timezone(TIMEZONE).to_date_string()
            == day.to_date_string()
        ]
        if not plants:
            # if not plants we return empty string
            return f"{day.to_date_string()} 的 Forst "
        return self.make_table_body(plants, day.to_date_string())

    def _init_plants(self):
        """
        TODO
        only support two days now?
        if I want to make the year repo to template
        I must support this
        """
        pass

    def make_daily_table(self):
        comments = list(self.issue.get_comments())
        today = pendulum.now(TIMEZONE)
        yesterday = pendulum.now(TIMEZONE).subtract(days=1)
        yesterday_body = self.make_plants_body(yesterday)
        today_body = self.make_plants_body(today)
        # this is the init forst things
        if not comments:
            # init it from start day of the year
            # TODO
            self._init_plants()
        else:
            latest_comment = comments[-1]
            latest_day = pendulum.instance(latest_comment.created_at).in_timezone(
                TIMEZONE
            )
            latest_issue_is_today = (latest_day.day == today.day) and (
                latest_day.month == today.month
            )
            latest_issue_is_yesterday = (latest_day.day == yesterday.day) and (
                latest_day.month == yesterday.month
            )
            if latest_issue_is_yesterday:
                latest_comment.edit(body=yesterday_body)
                # create today empty body then latest issue is today comment
                self.issue.create_comment(body=today_body)
            else:
                if latest_issue_is_today:
                    latest_comment.edit(body=today_body)
                else:
                    self.issue.create_comment(body=today_body)

    def make_forst_daily(self):
        end_date = pendulum.now(TIMEZONE)
        start_date = end_date.start_of("year")
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

        for p in periods:
            if p.to_date_string() not in self.log_days:
                break
            streak += 1
        # total plants, streak, is_today_check
        return len(self.plants), streak, is_today_check


def get_forst_daily(email, password, github_token, repo_name):
    f = Forst(email, password, github_token, repo_name)
    f.login()
    # also edit the issue body
    f.make_year_stats_table()
    f.make_daily_table()
    return f.make_forst_daily()
