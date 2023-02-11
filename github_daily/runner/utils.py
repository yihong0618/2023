import pendulum

from github_daily.config import TIMEZONE


def day_to_pendulum(day_string):
    """
    only support show today or yesterday for now
    if all return None istead
    """
    match day_string:
        case "today":
            return pendulum.today().in_timezone(TIMEZONE)
        case "yesterday":
            return pendulum.yesterday().in_timezone(TIMEZONE)
        case "all":
            return None
        case _:
            raise Exception("Only support today yesterday all for now")
