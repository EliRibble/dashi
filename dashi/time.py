import calendar
import datetime

ZERO = datetime.timedelta(0)
HOUR = datetime.timedelta(hours=1)

# A UTC class.
class UTC(datetime.tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO

def get_checkpoint(n):
    day_of_week = n.isoweekday()
    new_day = n - datetime.timedelta(days=(day_of_week-1))
    start = datetime.datetime(new_day.year, new_day.month, new_day.day, 0, 0, 0, 1, UTC())
    end = start + datetime.timedelta(days=7)
    return start, end

def checkpoints_since(start):
    now = datetime.datetime.utcnow()
    timepoint = start
    result = []
    in_a_week = datetime.timedelta(days=7)
    while timepoint < now + in_a_week:
        result.append(get_checkpoint(timepoint))
        timepoint = timepoint + in_a_week
    return result

def utcnow():
    return datetime.datetime.utcnow().replace(tzinfo=UTC())
