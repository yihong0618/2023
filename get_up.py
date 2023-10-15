import argparse
import os
import random

import openai
import pendulum
import requests
import telebot
from BingImageCreator import ImageGen
from github import Github
from telebot.types import InputMediaPhoto

# 20 for test 12 real get up
GET_UP_ISSUE_NUMBER = 20
GET_UP_MESSAGE_TEMPLATE = "今天的起床时间是--{get_up_time}.\r\n\r\n 起床啦，喝杯咖啡，背个单词，去跑步。\r\n\r\n 今天的一句诗:\r\n {sentence} \r\n"
SENTENCE_API = "https://v1.jinrishici.com/all"
DEFAULT_SENTENCE = "赏花归去马如飞\r\n去马如飞酒力微\r\n酒力微醒时已暮\r\n醒时已暮赏花归\r\n"
TIMEZONE = "Asia/Shanghai"


def login(token):
    return Github(token)


def get_one_sentence(up_list):
    try:
        r = requests.get(SENTENCE_API)
        if r.ok:
            concent = r.json().get("content")
            if concent in up_list:
                return get_one_sentence(up_list)
            return concent
        return DEFAULT_SENTENCE
    except:
        print("get SENTENCE_API wrong")
        return DEFAULT_SENTENCE


def get_today_get_up_status(issue):
    comments = list(issue.get_comments())
    if not comments:
        return False
    up_list = []
    for comment in comments:
        try:
            s = comment.body.splitlines()[6]
            up_list.append(s)
        except Exception as e:
            print(str(e), "!!")
            continue
    latest_comment = comments[-1]
    now = pendulum.now(TIMEZONE)
    latest_day = pendulum.instance(latest_comment.created_at).in_timezone(
        "Asia/Shanghai"
    )
    is_today = (latest_day.day == now.day) and (latest_day.month == now.month)
    return is_today, up_list


def make_pic_and_save(sentence):
    """
    return the link for md
    """
    # do not add text on the png
    sentence = sentence + ", textless"
    date_str = pendulum.now(TIMEZONE).to_date_string()
    new_path = os.path.join("OUT_DIR", date_str)
    if not os.path.exists(new_path):
        os.mkdir(new_path)
    response = openai.Image.create(prompt=sentence, n=1, size="1024x1024")
    image_url = response["data"][0]["url"]
    s = requests.session()
    index = 0
    while os.path.exists(os.path.join(new_path, f"{index}.jpeg")):
        index += 1
    with s.get(image_url, stream=True) as response:
        # save response to file
        response.raise_for_status()
        with open(os.path.join(new_path, f"{index}.jpeg"), "wb") as output_file:
            for chunk in response.iter_content(chunk_size=8192):
                output_file.write(chunk)
    image_url_for_issue = f"https://github.com/yihong0618/2023/blob/main/OUT_DIR/{date_str}/{index}.jpeg?raw=true"
    return image_url, image_url_for_issue


def make_pic_and_save(sentence, bing_cookie):
    # for bing image when dall-e3 open drop this function
    i = ImageGen(bing_cookie)
    images = i.get_images(sentence)
    date_str = pendulum.now().to_date_string()
    new_path = os.path.join("OUT_DIR", date_str)
    if not os.path.exists(new_path):
        os.mkdir(new_path)
    i.save_images(images, new_path)
    index = random.randint(0, len(images) - 1)
    image_url_for_issue = f"https://github.com/yihong0618/2023/blob/main/OUT_DIR/{date_str}/{index}.jpeg?raw=true"
    return images, image_url_for_issue


def make_get_up_message(bing_cookie, up_list):
    sentence = get_one_sentence(up_list)
    now = pendulum.now(TIMEZONE)
    # 3 - 7 means early for me
    is_get_up_early = 3 <= now.hour <= 24
    get_up_time = now.to_datetime_string()
    link_list = []
    try:
        link_list, link_for_issue = make_pic_and_save(sentence, bing_cookie)
    except Exception as e:
        print(str(e))
        # give it a second chance
        try:
            sentence = get_one_sentence(up_list)
            print(f"Second: {sentence}")
            link_list, link_for_issue = make_pic_and_save(sentence, bing_cookie)
        except Exception as e:
            print(str(e))
    body = GET_UP_MESSAGE_TEMPLATE.format(get_up_time=get_up_time, sentence=sentence)
    print(body, link_list, link_for_issue)
    return body, is_get_up_early, link_list, link_for_issue


def main(
    github_token,
    repo_name,
    bing_cookie,
    weather_message,
    tele_token,
    tele_chat_id,
):
    u = login(github_token)
    repo = u.get_repo(repo_name)
    issue = repo.get_issue(GET_UP_ISSUE_NUMBER)
    is_today, up_list = get_today_get_up_status(issue)
    if is_today:
        print("Today I have recorded the wake up time")
        return
    early_message, is_get_up_early, link_list, link_for_issue = make_get_up_message(
        bing_cookie, up_list
    )
    body = early_message
    if weather_message:
        weather_message = f"现在的天气是{weather_message}\n"
        body = weather_message + early_message
    if is_get_up_early:
        comment = body + f"![image]({link_for_issue})"
        issue.create_comment(comment)
        # send to telegram
        if tele_token and tele_chat_id:
            bot = telebot.TeleBot(tele_token)
            photos_list = [InputMediaPhoto(i, caption=body) for i in link_list]
            bot.send_media_group(tele_chat_id, photos_list)
    else:
        print("You wake up late")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("github_token", help="github_token")
    parser.add_argument("repo_name", help="repo_name")
    parser.add_argument(
        "--weather_message", help="weather_message", nargs="?", default="", const=""
    )
    parser.add_argument("bing_cookie", help="bing cookie")
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
        options.bing_cookie,
        options.weather_message,
        options.tele_token,
        options.tele_chat_id,
    )
