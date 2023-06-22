import time
import json
from deutsche_bahn_api.api_authentication import ApiAuthentication
from deutsche_bahn_api.station_helper import StationHelper
from deutsche_bahn_api.timetable_helper import TimetableHelper
import telepot
from telepot.loop import MessageLoop

#import header
import RPi.GPIO as GPIO
led =17

GPIO.setmode(GPIO.BCM)
GPIO.setup(led,GPIO.OUT)
led_pwm = GPIO.PWM(led, 1)

api = ApiAuthentication("4d92b50e16b9e7a97f9a95d55a08570e", "3ac2ae0cd903b5aa9315ebf338addbaf")
success: bool = api.test_credentials()
Bahnhof = "Hamburg Hbf"  # default station
Uhrzeit = 0  #

meinBahnhof = "Hamburg Hbf"  # starting trainstation has to exist to prevent errors
zielBahnhof = "0"
hour = 0
min = 0

watchdog_State = "S_OFF"

station_helper = StationHelper()
station_helper.load_stations()
# found_stations = station_helper.find_stations_by_lat_long(47.996713, 7.842174, 10)
found_stations_by_name = station_helper.find_stations_by_name(Bahnhof)
station = found_stations_by_name[0]

timetable_helper = TimetableHelper(station=station, api_authentication=api)
trains_in_this_hour = timetable_helper.get_timetable(Uhrzeit)
# trains_at_given_hour = timetable_helper.get_timetable(12)

trains_with_changes = timetable_helper.get_timetable_changes(trains_in_this_hour)


def updateBahnhof(Bahnhof, Uhrzeit):
    global found_stations_by_name, station, station_helper, timetable_helper, trains_in_this_hour, trains_with_changes
    station_helper = StationHelper()
    station_helper.load_stations()
    # found_stations = station_helper.find_stations_by_lat_long(47.996713, 7.842174, 10)
    timetable_helper = TimetableHelper(station=station, api_authentication=api)
    found_stations_by_name = station_helper.find_stations_by_name(Bahnhof)
    try:
        station = found_stations_by_name[0]

    except:
        return 0
    trains_in_this_hour = timetable_helper.get_timetable(Uhrzeit)
    trains_with_changes = timetable_helper.get_timetable_changes(trains_in_this_hour)

    return 1  # no error

def updateUhrzeit(Uhrzeit):
    global found_stations_by_name, station, station_helper, timetable_helper, trains_in_this_hour, trains_with_changes
    station_helper = StationHelper()
    station_helper.load_stations()
    # found_stations = station_helper.find_stations_by_lat_long(47.996713, 7.842174, 10)

    timetable_helper = TimetableHelper(station=station, api_authentication=api)
    trains_in_this_hour = timetable_helper.get_timetable(Uhrzeit)
    # trains_at_given_hour = timetable_helper.get_timetable(12)

    trains_with_changes = timetable_helper.get_timetable_changes(trains_in_this_hour)

    return 1  # no error


telegram_bot_token = '5903546968:AAGV8-1QjiyYa3SpGh0R_QfC_N0rxB7OUvs'

# Chat-ID des Empfängers - Lukas Bot aktuell
telegram_chat_id = '5877570960'


def reverse_split(string):
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
    if hasattr(train.train_changes, "departure"):

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


def handle_messages(msg):
    global Bahnhof, found_stations_by_name, station, station_helper, timetable_helper, trains_in_this_hour, trains_with_changes, Uhrzeit
    global meinBahnhof, zielBahnhof, hour, min, watchdog_State
    content_type, chat_type, chat_id = telepot.glance(
        msg)  # Python-Telegram function that returns the values message type, chat type  and chat id from a telegram message
    if content_type == 'text':  # glance checks the message type. If the type is in the form of text, we have a valid message
        if msg['text'] == 'Züge':  # user input
            for i, train in enumerate(trains_in_this_hour):
                message = f"Zug {i + 1} \n departure= {reverse_split(train.departure)} \n  platform = {train.platform} \n stations = {train.stations} \n  " \
                          f"train_number = {train.train_number} \n train_type = {train.train_type} \n "

                bot.sendMessage(telegram_chat_id, message)

        if msg['text'] == 'hilfe':  # user is kind
            # message = f"Menü:\n1. Züge - zeigt alle züge in der angegebenen Stunde an\n2. Bahnhof [neuer Bahnhof]\n ändert den aktuellen Bahnhof\n" \
            #          f"3. Uhrzeit [neue Uhrzeit]\n ändert die Uhrezit für den Zeitplan.\n Für die aktuelle Uhrzeit 0 eingeben\n"  # bot prepares a welcoming message
            message = f"Menü:\n" \
                      f"1. Züge\n" \
                      f"   - zeigt alle züge in der angegebenen Stunde an\n\n" \
                      f"2. Bahnhof [neuer Bahnhof]\n" \
                      f"   - ändert den aktuellen Bahnhof\n\n" \
                      f"3. Uhrzeit [neue Uhrzeit(stunde)]\n" \
                      f"   - ändert die Uhrzeit für den Zeitplan.Für die aktuelle Uhrzeit 0 eingeben\n\n" \
                      f"4. Verspätung\n" \
                      f"   - zeigt alle Verspätungen am eingestellten Bahnhof zur eingestellten Uhrzeit an.\n\n" \
                      f"5. watch:[start Bahnhof]:[ziel Bahnhof]:[Stunde]:[Minute]\n" \
                      f"   - startet die Überwachung für die gegebene Zugverbindung. Sobald eine Verspätung von über" \
                      f" 5 Minuten erkannt wurde, wird eine Nachricht geschickt und die Überwachung beendet." \
                      f"6. info\n" \
                      f"   - zeigt den eingestellten Bahnhof und Uhrzeit an."
            bot.sendMessage(telegram_chat_id, message)  # and sends it

        if msg['text']:  # handle Bahnhof command
            message = msg['text']
            if message.startswith('Bahnhof'):  # set station
                Bahnhof = message.split(' ', 1)[1]
                if updateBahnhof(Bahnhof, Uhrzeit) == 1:
                    updateBahnhof(Bahnhof, Uhrzeit)
                    message = "Dein gewählter Bahnhof ist: " + Bahnhof
                    bot.sendMessage(telegram_chat_id, message)  # and sends it
                else:
                    message = "Fehlerhafte Eingabe. Bitte überprüfe den Namen des Bahnhofs."
                    bot.sendMessage(telegram_chat_id, message)  # and sends it

        if msg['text']:  # handle Uhrzeit command
            message = msg['text']
            if message.startswith('Uhrzeit'):  # set station
                buffer = message.split(' ', 1)[1]
                if buffer.isnumeric():  # check if there are only numbers in the string
                    if 0 <= int(buffer) <= 24:
                        Uhrzeit = buffer    # if everything is alright write to global variable
                        updateUhrzeit(Uhrzeit)
                        message = f"Deine gewählte Uhrzeit ist: {buffer}:00 Uhr"

                    else:
                        message = "Fehlerhafte Eingabe der Uhrzeit. Bitte nur eine maximal zweistellige Stundenzahl eingeben."
                else:
                    message = "Fehlerhafte Eingabe der Uhrzeit. Bitte nur Zahlen eingeben.\n" \
                              "Beispiel: Uhrzeit 17"
                bot.sendMessage(telegram_chat_id, message)  # and sends it

        if msg['text'] == 'Verspätung':  # handle Verspäterung command
            for i, train in enumerate(trains_with_changes):
                if delay(train) >= 5:
                    message = f"Zug {i + 1} \nold departure= {reverse_split(train.departure)} \nnew departure= {reverse_split(train.train_changes.departure)}\n" \
                              f"Verspätung = {delay(train)} Minuten\n" \
                              f"platform = {train.platform} \nstations = {train.stations} \n" \
                              f"train_number = {train.train_number} \ntrain_type = {train.train_type} \n "
                    bot.sendMessage(telegram_chat_id, message)  # and sends it

        if msg['text']:  # handle watch command
            message = msg['text']
            if message.startswith('watch'):  # user input is divided with ":". Filtering the given information for futher processing
                meinBahnhof = message.split(':', 4)[1]
                zielBahnhof = message.split(':', 4)[2]
                hour = message.split(':', 4)[3]
                min = message.split(':', 4)[4]
                if hour.isnumeric() and min.isnumeric() ==1:    #error handling: only numbers for time input allowed
                    hour = int(hour)
                    min = int(min)
                    try:
                        station_helper.find_stations_by_name(meinBahnhof)[0]  # check if start station name exists
                        station_helper.find_stations_by_name(zielBahnhof)[0]  # check if end station name exists
                        if 0 <= hour <= 24 and 0 <= min <= 60:  #only specific numbers allowed
                            trains_at_given_hour = timetable_helper.get_timetable(hour) #get train data from api
                            trains_with_changes = timetable_helper.get_timetable_changes(trains_at_given_hour)
                            flag =0 #flag to check if train actually exists

                            for i, train in enumerate(trains_with_changes): #check all trains in given hour to find if the one at given hour+minute exists

                                if str(hour)+str(min) in train.departure and zielBahnhof in train.stations:
                                    message = f"Überwachung gestartet:{meinBahnhof} - {zielBahnhof} um {hour}:{min} Uhr"
                                    flag =1 # train detected
                                    bot.sendMessage(telegram_chat_id, message)  # and sends it
                                    watchdog_State = "S_ON"
                            if flag == 0:   #no train detected
                                message = f"Die gewählte Zugverbindung existiert nicht. Bitte Eingabe überprüfen."
                                bot.sendMessage(telegram_chat_id, message)  # and sends it
                        else:
                            message = f"Fehlerhafte Eingabe. Bitte überprüfe die eingegebene Uhrzeit."
                            bot.sendMessage(telegram_chat_id, message)  # and sends it

                    except:
                        message = f"Fehlerhafte Eingabe. Bitte überprüfe die Namen der Bahnhöfe."
                        bot.sendMessage(telegram_chat_id, message)  # and sends it
                else:
                    message = f"Fehlerhafte Eingabe. Bitte überprüfe die eingegebene Uhrzeit."
                    bot.sendMessage(telegram_chat_id, message)  # and sends it

            if msg['text'] == 'info':
                if Uhrzeit == 0:
                    message = f"Eingestellter Bahnhof: {Bahnhof}\n" \
                              f"Eingestellte Uhrzeit: aktuelle Uhrzeit"
                else:
                    message = f"Eingestellter Bahnhof: {Bahnhof}\n" \
                              f"Eingestellte Uhrzeit: {Uhrzeit}:00 Uhr"
                bot.sendMessage(telegram_chat_id, message)  # and sends it

            if msg['text'] == 'LED off':
                led_pwm.stop()
                led_pwm.ChangeDutyCycle(50) #another initialization needed to make things work again
                led_pwm.ChangeFrequency(1)

                message = f"Alarm wurde ausgestellt."
                bot.sendMessage(telegram_chat_id, message)

def watchdog(start, ziel, hour, min):
    global watchdog_State,LED_STATE
    departure = str(hour) + str(min)
    if "S_ON" == watchdog_State:
        station_helper = StationHelper()
        station_helper.load_stations()
        # found_stations = station_helper.find_stations_by_lat_long(47.996713, 7.842174, 10)
        found_stations_by_name = station_helper.find_stations_by_name(start)
        station = found_stations_by_name[0]

        timetable_helper = TimetableHelper(station=station, api_authentication=api)
        trains_at_given_hour = timetable_helper.get_timetable(hour)
        trains_with_changes = timetable_helper.get_timetable_changes(trains_at_given_hour)

        for i, train in enumerate(trains_with_changes):
            if ziel in train.stations:
                if departure in train.departure:  # identifying the train by planned time
                    if delay(train) >= 5:
                        message = f"Dein Zug um {reverse_split(train.departure)[0:5]} Uhr von {start} nach " \
                                  f"{ziel} hat eine Verspätung von {delay(train)} minuten.\n" \
                                  f"Die neue Abfahrtzeit ist {reverse_split(train.train_changes.departure)[0:5]} Uhr."
                        bot.sendMessage(telegram_chat_id, message)  # and sends it
                        watchdog_State = "S_OFF"

                        return 1
        return 0


# initialize Telegram-Bot
bot = telepot.Bot(telegram_bot_token)  # my bot is the bot with this token
bot.getMe()
bot.getUpdates()

# message handle for  the telegram bot
MessageLoop(bot, handle_messages).run_as_thread()

while 1:
    if(watchdog(meinBahnhof, zielBahnhof, hour, min)):
        led_pwm.start(50)

