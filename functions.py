#   Header with all self-written fuctions to calculate values, form strings etc.

def reverse_split(string):
    #   API gives time and day in formation: year/month/day/hour/min
    #   to make this information easier to read for the user a seperation and rearangement of the string
    #   is required

    msg_year = string[0];  # year
    msg_year2 = string[1];  # year

    msg_month = string[2];  # month
    msg_month2 = string[3];  # month

    msg_day = string[4];  # day
    msg_day2 = string[5];  # day

    msg_hour = string[6];  # hour
    msg_hour2 = string[7];  # hour

    msg_minute = string[8];  # minute
    msg_minute2 = string[9];  # minute

    msg = msg_hour + msg_hour2 + ":" + msg_minute + msg_minute2 + "   " + msg_day + msg_day2 + "." + msg_month + msg_month2 + "." + msg_year + msg_year2
    return msg

def delay(train):
    #   Each train which is given by the API has the attribute departure. BUT every train with changes has an
    #   attribute list called train_changes. Inside this list there is also a attribute called departure
    #   with the delayed, new departure. To calculate the train delay in total a comparison of these two
    #   departure values are necessary.

    if hasattr(train.train_changes, "departure"):   #   Check if given train has a delay. Sometimes trains have changes without delay.

        hour2 = train.train_changes.departure[6] + train.train_changes.departure[7]  # new departure hour
        hour1 = train.departure[6] + train.departure[7]  # old departure hour

        min2 = train.train_changes.departure[8] + train.train_changes.departure[9]  # new departure min
        min1 = train.departure[8] + train.departure[9]  # old departure min

        hour = int(hour2) - int(hour1)  # calculate how many hours/mins delay
        min = int(min2) - int(min1)
        delay = hour * 60 + min  # convert to mins

        return delay
    else:
        return 0