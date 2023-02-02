use std::borrow::Borrow;

use anyhow::Result;
use chrono::prelude::*;
use chrono::{self, Timelike};
use clap::{Args, Parser};
use octocrab::OctocrabBuilder;
use serde::Deserialize;

static DEFAULT_SENTENCE: &str =
    "赏花归去马如飞\r\n去马如飞酒力微\r\n酒力微醒时已暮\r\n醒时已暮赏花归\r\n";

static GET_UP_ISSUE_NUMBER: u64 = 13u64;

#[derive(Debug, Deserialize)]
struct SentenceResponse {
    content: String,
}

async fn get_one_sentence() -> Result<String> {
    let api = "https://v1.jinrishici.com/all";
    let resp = reqwest::get(api).await?.json::<SentenceResponse>().await?;
    Ok(resp.content)
}

fn make_get_up_message(weather: Option<String>, date: String, sentence: String) -> Result<String> {
    Ok("今天的起床时间是：".to_string()
        + "\r\n"
        + &weather.unwrap_or_default().to_string()
        + "\r\n"
        + &date
        + "\r\n\r\n"
        + &sentence)
}

async fn make_new_issue(opts: GetUpOpts) -> Result<()> {
    let mut sentence = get_one_sentence()
        .await
        .unwrap_or(DEFAULT_SENTENCE.to_string());
    let mut s = opts.repo_name.split("/");
    let owner = s.next().unwrap_or_default();
    let repo = s.next().unwrap_or_default();
    let wether_message = opts.wether_message;

    octocrab::initialise(OctocrabBuilder::new().personal_token(opts.github_token.to_string()))?;
    // TODO comments maybe upper than 100 need page
    let comments = octocrab::instance()
        .issues(owner, repo)
        .list_comments(GET_UP_ISSUE_NUMBER)
        .send()
        .await?;
    let comment = comments.items.last();
    let tz = chrono::FixedOffset::east_opt(3600 * 8).unwrap();
    let today = Utc::now().with_timezone(&tz);
    sentence = make_get_up_message(wether_message, today.to_string(), sentence).unwrap();
    if comment.is_none() {
        octocrab::instance()
            .issues(owner, repo)
            .create_comment(GET_UP_ISSUE_NUMBER, sentence)
            .await?;
    } else {
        let get_up_time = comment.unwrap().created_at.borrow().with_timezone(&tz);
        let last_issue_day = get_up_time.date_naive();
        let get_up_hour = get_up_time.hour();
        if today.date_naive().to_string() != last_issue_day.to_string()
            && get_up_hour >= 5
            && get_up_hour <= 24
        {
            octocrab::instance()
                .issues(owner, repo)
                .create_comment(GET_UP_ISSUE_NUMBER, sentence)
                .await?;
        }
    }
    Ok(())
}

#[tokio::main]
async fn main() -> Result<()> {
    let app_opts = AppOpts::parse();
    match app_opts {
        AppOpts::GetUp(get_up_opts) => {
            make_new_issue(get_up_opts).await?;
        }
    }
    Ok(())
}

#[derive(Debug, Parser, Clone)]
#[clap(about, version, author)]
enum AppOpts {
    GetUp(GetUpOpts),
}

#[derive(Debug, Args, Clone)]
struct GetUpOpts {
    github_token: String,
    repo_name: String,

    /// custom weather message
    wether_message: Option<String>,
    /// telegram bot token
    tele_token: Option<String>,
    /// telegram chat id
    tele_chat_id: Option<String>,
}
