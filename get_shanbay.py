import argparse

import pendulum
import requests
from github import Github

# set up your shanbay issue index
GET_UP_ISSUE_NUMBER = ""
# update your own shanbay user_name
SHANBAY_USERNAME = ""

SHANBAY_API = f"https://apiv3.shanbay.com/uc/checkin/logs?user_id={SHANBAY_USERNAME}&ipp=10&page=1"
SHANBAY_RECORD_MESSAGE = "打卡日期 {learn_date}\r\n学习 {used_minutes} 分钟，背单词 {num} 个"
DEFAULT_RECORD = "获取扇贝记录出错啦，检查检查代码吧"

TIMEZONE = "Asia/Shanghai"


def login(token):
    return Github(token)


def get_today_get_up_status(issue):
    comments = list(issue.get_comments())

    if not comments:
        return False

    latest_comment = comments[-1]
    now = pendulum.now(TIMEZONE)
    latest_day = pendulum.instance(latest_comment.created_at).in_timezone(
        "Asia/Shanghai"
    )
    is_today = (latest_day.day == now.day) and (latest_day.month == now.month)
    return is_today


def get_latest_record():
    try:
        r = requests.get(SHANBAY_API)
        if r.ok:
            record_list = r.json().get("objects")
            if len(record_list) > 0:
                # get the latest one
                latest_record = record_list[0]
                learn_date = latest_record.get("date")
                task = latest_record.get("tasks")[0]
                # get reciting words number
                num = task.get("num")
                used_time = task.get("used_time")

                used_minutes, s = divmod(used_time, 60)

                return SHANBAY_RECORD_MESSAGE.format(
                    learn_date=learn_date, used_minutes=used_minutes, num=num
                )
    except:
        print("get SHANBAY_API wrong")
        return DEFAULT_RECORD


def main(github_token, repo_name):
    u = login(github_token)
    repo = u.get_repo(repo_name)
    issue = repo.get_issue(GET_UP_ISSUE_NUMBER)
    is_toady = get_today_get_up_status(issue)
    body = get_latest_record()

    if is_toady:
        comment = list(issue.get_comments())[-1]
        comment.edit(body)
    else:
        issue.create_comment(body)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("github_token", help="github_token")
    parser.add_argument("repo_name", help="repo_name")

    options = parser.parse_args()
    main(
        options.github_token,
        options.repo_name,
    )
