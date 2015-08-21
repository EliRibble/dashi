import calendar
import datetime

def get_checkpoint(n):
    day_of_week = n.isoweekday()
    new_day = n - datetime.timedelta(days=(day_of_week-1))
    start = datetime.datetime(new_day.year, new_day.month, new_day.day, 0, 0, 0, 1)
    end = start + datetime.timedelta(days=7)
    return start, end

def checkpoints_since(start):
    now = datetime.datetime.utcnow()
    timepoint = start
    result = []
    in_a_week = datetime.timedelta(days=7)
    while timepoint < now + in_a_week:
        result.append((timepoint, timepoint + in_a_week))
        timepoint = timepoint + in_a_week
    return result
