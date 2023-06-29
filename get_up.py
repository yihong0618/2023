import argparse
import os

import pendulum
import requests
from github import Github
import random
import openai
from BingImageCreator import ImageGen

# 14 for test 12 real get up
GET_UP_ISSUE_NUMBER = 12
GET_UP_MESSAGE_TEMPLATE = "今天的起床时间是--{get_up_time}.\r\n\r\n 起床啦，喝杯咖啡，背个单词，去跑步。\r\n\r\n 今天的一句诗:\r\n {sentence} \r\n  ![image]({link})"
SENTENCE_API = "https://v1.jinrishici.com/all"
DEFAULT_SENTENCE = "赏花归去马如飞\r\n去马如飞酒力微\r\n酒力微醒时已暮\r\n醒时已暮赏花归\r\n"
TIMEZONE = "Asia/Shanghai"
PROMPT = "请帮我把这个句子 `{sentence}` 翻译成英语，请按描述绘画的方式翻译，只返回翻译后的句子"


def login(token):
    return Github(token)


def get_one_sentence():
    try:
        r = requests.get(SENTENCE_API)
        if r.ok:
            return r.json().get("content", DEFAULT_SENTENCE)
        return DEFAULT_SENTENCE
    except:
        print("get SENTENCE_API wrong")
        return DEFAULT_SENTENCE


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


def make_pic_and_save(sentence_en, bing_cookie):
    """
    return the link for md
    """
    i = ImageGen(bing_cookie)
    images = i.get_images(sentence_en)
    date_str = pendulum.now().to_date_string()
    new_path = os.path.join("OUT_DIR", date_str)
    if not os.path.exists(new_path):
        os.mkdir(new_path)
    # download count = 4
    i.save_images(images, new_path)
    return random.choice(images)


def make_get_up_message(bing_cookie):
    sentence = get_one_sentence()
    now = pendulum.now(TIMEZONE)
    # 3 - 7 means early for me
    is_get_up_early = 3 <= now.hour <= 7
    get_up_time = now.to_datetime_string()
    ms = [{"role": "user", "content": PROMPT.format(sentence=sentence)}]
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=ms,
    )
    sentence_en = (
        completion["choices"][0].get("message").get("content").encode("utf8").decode()
    )
    link = ""
    try:
        link = make_pic_and_save(sentence_en, bing_cookie)
    except Exception as e:
        print(str(e))
    body = GET_UP_MESSAGE_TEMPLATE.format(
        get_up_time=get_up_time, sentence=sentence, link=link
    )
    print(body)
    return body, is_get_up_early


def main(
    github_token, repo_name, weather_message, bing_cookie, tele_token, tele_chat_id
):
    u = login(github_token)
    repo = u.get_repo(repo_name)
    issue = repo.get_issue(GET_UP_ISSUE_NUMBER)
    is_toady = get_today_get_up_status(issue)
    if is_toady:
        print("Today I have recorded the wake up time")
        return
    early_message, is_get_up_early = make_get_up_message(bing_cookie)
    body = early_message
    if weather_message:
        weather_message = f"现在的天气是{weather_message}\n"
        body = weather_message + early_message
    if is_get_up_early:
        issue.create_comment(body)
        # send to telegram
        if tele_token and tele_chat_id:
            requests.post(
                url="https://api.telegram.org/bot{0}/{1}".format(
                    tele_token, "sendMessage"
                ),
                data={
                    "chat_id": tele_chat_id,
                    "text": body,
                },
            )
    else:
        print("You wake up late")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("github_token", help="github_token")
    parser.add_argument("repo_name", help="repo_name")
    parser.add_argument(
        "--weather_message", help="weather_message", nargs="?", default="", const=""
    )
    parser.add_argument(
        "--bing_cookie", help="bing_cookie", nargs="?", default="", const=""
    )
    parser.add_argument(
        "--tele_token", help="tele_token", nargs="?", default="", const=""
    )
    parser.add_argument(
        "--tele_chat_id", help="tele_chat_id", nargs="?", default="", const=""
    )
    options = parser.parse_args()
    main(
        options.github_token,
        options.repo_name,
        options.weather_message,
        options.bing_cookie,
        options.tele_token,
        options.tele_chat_id,
    )
