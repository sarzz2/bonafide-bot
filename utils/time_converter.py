time_convert = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def convert_time_to_seconds(time):
    try:
        return int(time[:-1]) * time_convert[time[-1]]
    except:
        raise ValueError
