# 2023.02.07 for now just for me, that make a cli eaisy to use 2023
# lets call it gh2023
# use Python for now maybe Rust in the future
import argparse

from github_daily.runner import (
    ForstRunner,
    GTDRunner,
    IdeaRunner,
    ReadRunner,
    TimelineRunner,
    PushupRunner,
)


def main():
    # TODO refactor this like GitHubPoster
    args_parser = argparse.ArgumentParser()
    subparser = args_parser.add_subparsers(dest="command")
    ########### GTD RUNNER ###########
    gtd = subparser.add_parser(name="gtd")
    gtd.set_defaults(runner=GTDRunner)

    gtd.add_argument(
        "-s",
        "--show",
        dest="show",
        type=str,
        default="today",
        choices=["today", "yesterday", "all"],
        help="show today forst table",
    )
    gtd.add_argument(
        "-a",
        "--add",
        dest="add",
        type=str,
        help="to do stringto add",
    )

    gtd.add_argument(
        "-d",
        "--done",
        dest="done",
        type=int,
        help="which to do to be done",
    )
    gtd.add_argument(
        "-ud",
        "--undone",
        dest="undone",
        type=int,
        help="which to do to be undone",
    )
    ########### FORST RUNNER ###########
    forst = subparser.add_parser(name="forst")
    forst.add_argument(
        "-s",
        "--show",
        dest="show",
        type=str,
        default="today",
        choices=["today", "yesterday", "all"],
        help="show today forst table",
    )
    forst.add_argument(
        "-sy",
        "--sync",
        dest="sync",
        action="store_true",
        help="if to sync the forst to GitHub",
    )
    forst.set_defaults(runner=ForstRunner)

    ########### IDEA RUNNER ###########
    idea = subparser.add_parser(name="idea")
    idea.add_argument(
        "-s",
        "--show",
        dest="show",
        type=str,
        default="all",
        choices=["all", "today"],
        help="show today or all idea as table",
    )
    idea.add_argument(
        "-a",
        "--add",
        dest="add",
        type=str,
        help="idea to add",
    )
    idea.set_defaults(runner=IdeaRunner)

    ########### READ RUNNER ###########
    read = subparser.add_parser(name="read")
    read.add_argument(
        "-s",
        "--show",
        dest="show",
        type=str,
        default="all",
        choices=["all", "today"],
        help="show today or all read as table",
    )
    read.add_argument(
        "-a",
        "--add",
        dest="add",
        type=str,
        help="read to add",
    )
    read.set_defaults(runner=ReadRunner)

    ########### TiMELINE RUNNER ###########
    timeline = subparser.add_parser(name="timeline")
    timeline.add_argument(
        "-s",
        "--show",
        dest="show",
        type=str,
        default="all",
        choices=["all", "today"],
        help="show today or all timeline as table",
    )
    timeline.add_argument(
        "-a",
        "--add",
        dest="add",
        type=str,
        help="timeline to add",
    )
    timeline.set_defaults(runner=TimelineRunner)
    ########### Pushup RUNNER ###########
    pushup = subparser.add_parser(name="pushup")
    pushup.add_argument(
        "-s",
        "--show",
        dest="show",
        type=str,
        default="all",
        choices=["all", "today"],
        help="show today or all timeline as table",
    )
    pushup.add_argument(
        "-a",
        "--add",
        dest="add",
        type=str,
        help="push up to add",
    )
    pushup.set_defaults(runner=PushupRunner)

    args = args_parser.parse_args()
    # all runner
    runner = args.runner()
    if args.show:
        runner.show_day = args.show
        runner.show()
    match args.command:
        case "gtd":
            if args.add:
                runner.add(args.add)
            else:
                if args.done:
                    runner.done_or_undone(args.done, is_done=True)
                if args.undone:
                    runner.done_or_undone(args.undone, is_done=False)
        case "forst":
            if args.sync:
                runner.sync()
        case "idea" | "read" | "timeline" | "pushup":
            if args.add:
                runner.add(args.add)
        case _:
            print("Not support for now")


if __name__ == "__main__":
    main()
