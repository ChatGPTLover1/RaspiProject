#   HAW Hamburg - Raspberry Pi, Summer Semester 2023
#   Author: Linus Kohlmann, Lukas Rabuske, Selin Valerie
#   Last edit: 23.06.2023
#
#   Python program which is using the 'deutsche-bahn-api' to receive data regarding (delayed) trains.
#   The communication between user and program is happening by using a telegram bot. The necessary data can be edited
#   in the telegramData.py file. The program is meant to be run on a raspberry pi to also make use of the
#   GPIO output.
#
#   The bot can give information about the trains at a given train station and given hour. It is also possible to
#   filter the output to only get information about delayed trains.
#   There is also a watchdog function which will monitor one specific train connection. If a delay gets detected,
#   the user will get notified by the bot and also a LED will start to flash.

from deutsche_bahn_api.api_authentication import ApiAuthentication
from deutsche_bahn_api.station_helper import StationHelper
from deutsche_bahn_api.timetable_helper import TimetableHelper
import telepot
from telepot.loop import MessageLoop
import RPi.GPIO as GPIO

#   Selfmade files to import
import telegramData
import functions

#   configuring the GPIO/LED
led =17     #   Using GPIO 17
dutyCycle= 50   #   LED on and off time should be equal
Frequency = 1   #   LED flashing with 1Hz
GPIO.setmode(GPIO.BCM)
GPIO.setup(led,GPIO.OUT)
led_pwm = GPIO.PWM(led, Frequency)  #

#   entering key to get acces to api
api = ApiAuthentication("4d92b50e16b9e7a97f9a95d55a08570e", "3ac2ae0cd903b5aa9315ebf338addbaf")
success: bool = api.test_credentials()  #   test if access to api is working

#   config values for the bot
Bahnhof = "Hamburg Hbf"  # default station
Uhrzeit = 0  # Time(hour) at which the bot is looking for trains. 0 is the current time.
delayThreshhold = 5 # Threshhold at which a delay should be recognized when crossed.

meinBahnhof = "Hamburg Hbf"  # starting trainstation for watchdog. Has to exist to prevent errors.
zielBahnhof = "0"   # Watchdog destination trainstation
hour = 0    # Watchdog time (hour). Will be given by user.
min = 0 # Watchdog time (min). Will be given by user.
watchdog_State = "S_OFF"    # watchdog is handled by states. Initially off.


#   fetching information once the bot has been started.
station_helper = StationHelper()
station_helper.load_stations()
found_stations_by_name = station_helper.find_stations_by_name(Bahnhof)  #looking for the trainstation
station = found_stations_by_name[0] # first entry in array is the station name. Used to check if given station name is valid.
timetable_helper = TimetableHelper(station=station, api_authentication=api) #calling the api

trains_in_this_hour = timetable_helper.get_timetable(Uhrzeit)   #getting the timetable at given time
trains_with_changes = timetable_helper.get_timetable_changes(trains_in_this_hour)   #getting all trains with changes at given time


def updateBahnhof(Bahnhof, Uhrzeit):
    #   function to update the trainstation and update the timetable with given trainstation.
    global found_stations_by_name, station, station_helper, timetable_helper, trains_in_this_hour, trains_with_changes

    # calling api again
    station_helper = StationHelper()
    station_helper.load_stations()
    timetable_helper = TimetableHelper(station=station, api_authentication=api)
    found_stations_by_name = station_helper.find_stations_by_name(Bahnhof)

    try:    #checking if given trainstation name is valid
        station = found_stations_by_name[0]

    except:
        return 0    #error, invalid station name

    trains_in_this_hour = timetable_helper.get_timetable(Uhrzeit)
    trains_with_changes = timetable_helper.get_timetable_changes(trains_in_this_hour)

    return 1  # no error

def updateUhrzeit(Uhrzeit):
    #   function to update the time for the timetable.
    global found_stations_by_name, station, station_helper, timetable_helper, trains_in_this_hour, trains_with_changes

    #calling api
    station_helper = StationHelper()
    station_helper.load_stations()
    timetable_helper = TimetableHelper(station=station, api_authentication=api)
    trains_in_this_hour = timetable_helper.get_timetable(Uhrzeit)
    trains_with_changes = timetable_helper.get_timetable_changes(trains_in_this_hour)

def handle_messages(msg):
    # message handler for telegram bot. Communication between user and bot is happening here

    global Bahnhof, found_stations_by_name, station, station_helper, timetable_helper, trains_in_this_hour, trains_with_changes, Uhrzeit
    global meinBahnhof, zielBahnhof, hour, min, watchdog_State

    content_type, chat_type, chat_id = telepot.glance(msg)
    if content_type == 'text':

        if msg['text'] == 'Züge':
            # Checking all trains at the selected time and trainstation and gives information for all trains
            for i, train in enumerate(trains_in_this_hour):
                message = f"Zug {i + 1} \n departure= {functions.reverse_split(train.departure)} \n  platform = {train.platform} \n stations = {train.stations} \n  " \
                          f"train_number = {train.train_number} \n train_type = {train.train_type} \n "

                bot.sendMessage(telegramData.telegram_chat_id, message)

        if msg['text'] == 'hilfe':
            # helping menue
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
                      f" 5 Minuten erkannt wurde, wird eine Nachricht geschickt, LED fängt an zu" \
                      f" blinken und die Überwachung wird beendet." \
                      f" Die angeschlossene LED blinkt so lange bis sie per Kommando gestoppt wird.\n\n" \
                      f"6. LED off\n" \
                      f"   - schaltet die LED aus.\n\n" \
                      f"7. info\n" \
                      f"   - zeigt den eingestellten Bahnhof und Uhrzeit an."
            bot.sendMessage(telegramData.telegram_chat_id, message)  # and sends it

        if msg['text']:  # handle Bahnhof command
            message = msg['text']
            if message.startswith('Bahnhof'):  # set station
                Bahnhof = message.split(' ', 1)[1]  # cut away the first word (Bahnhof) in the user message
                if updateBahnhof(Bahnhof, Uhrzeit) == 1:    # if entered trainstation is valid, trainstation will get updated
                    updateBahnhof(Bahnhof, Uhrzeit)
                    message = "Dein gewählter Bahnhof ist: " + Bahnhof
                    bot.sendMessage(telegramData.telegram_chat_id, message)  # and sends it
                else:   # error handling
                    message = "Fehlerhafte Eingabe. Bitte überprüfe den Namen des Bahnhofs."
                    bot.sendMessage(telegramData.telegram_chat_id, message)  # and sends it

        if msg['text']:  # handle Uhrzeit command
            message = msg['text']
            if message.startswith('Uhrzeit'):  # set station
                buffer = message.split(' ', 1)[1]   # cut away the first word (Uhrzeit) in the user message
                if buffer.isnumeric():  # check if there are only numbers in the string
                    if 0 <= int(buffer) <= 24:  # there are only 24 hours in a day. check if user input is correct
                        Uhrzeit = buffer    # if everything is alright write to global variable
                        updateUhrzeit(Uhrzeit)
                        message = f"Deine gewählte Uhrzeit ist: {buffer}:00 Uhr"

                    else:   #error handling, user gets notified
                        message = "Fehlerhafte Eingabe der Uhrzeit. Bitte nur eine maximal zweistellige Stundenzahl eingeben."
                else: #error handling, user gets notified with example on how to use the command correctly
                    message = "Fehlerhafte Eingabe der Uhrzeit. Bitte nur Zahlen eingeben.\n" \
                              "Beispiel: Uhrzeit 17"
                bot.sendMessage(telegramData.telegram_chat_id, message)  # and sends it

        if msg['text'] == 'Verspätung':  # handle Verspäterung command
            delayFlag= False # flag used to handle cases where there are no delays
            for i, train in enumerate(trains_with_changes):
                if functions.delay(train) >= delayThreshhold:   # look for all trains with relevant delay
                    message = f"Zug {i + 1} \nold departure= {functions.reverse_split(train.departure)} \nnew departure= {functions.reverse_split(train.train_changes.departure)}\n" \
                              f"Verspätung = {functions.delay(train)} Minuten\n" \
                              f"platform = {train.platform} \nstations = {train.stations} \n" \
                              f"train_number = {train.train_number} \ntrain_type = {train.train_type} \n "
                    delayFlag=True
                    bot.sendMessage(telegramData.telegram_chat_id, message)  # and sends it
            if delayFlag:
                message = f"Keine Verspätung vorhanden"
                bot.sendMessage(telegramData.telegram_chat_id, message)  # and sends it


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
                            trains_with_changes = timetable_helper.get_timetable_changes(trains_at_given_hour) # get trains with changes
                            flag =0 #flag to check if train actually exists

                            for i, train in enumerate(trains_with_changes): #check all trains in given hour to find if the one at given hour+minute exists

                                if str(hour)+str(min) in train.departure and zielBahnhof in train.stations: # check if train from user inout exists
                                    message = f"Überwachung gestartet:{meinBahnhof} - {zielBahnhof} um {hour}:{min} Uhr"
                                    flag =1 # train detected
                                    bot.sendMessage(telegramData.telegram_chat_id, message)  # and sends it
                                    watchdog_State = "S_ON" # train detected -> watchdog switching on
                            if flag == 0:   #error handling, no train detected
                                message = f"Die gewählte Zugverbindung existiert nicht. Bitte Eingabe überprüfen."
                                bot.sendMessage(telegramData.telegram_chat_id, message)  # and sends it
                        else:   #error handling, false input (time)
                            message = f"Fehlerhafte Eingabe. Bitte überprüfe die eingegebene Uhrzeit."
                            bot.sendMessage(telegramData.telegram_chat_id, message)  # and sends it

                    except: #error handling, false input (trainstation)
                        message = f"Fehlerhafte Eingabe. Bitte überprüfe die Namen der Bahnhöfe."
                        bot.sendMessage(telegramData.telegram_chat_id, message)  # and sends it
                else: #error handling, false input (time)
                    message = f"Fehlerhafte Eingabe. Bitte überprüfe die eingegebene Uhrzeit."
                    bot.sendMessage(telegramData.telegram_chat_id, message)  # and sends it

            if msg['text'] == 'info':
                # give information on selected trainstation on time
                if Uhrzeit == 0: # as given by the api, 0 is the current time
                    message = f"Eingestellter Bahnhof: {Bahnhof}\n" \
                              f"Eingestellte Uhrzeit: aktuelle Uhrzeit"
                else:
                    message = f"Eingestellter Bahnhof: {Bahnhof}\n" \
                              f"Eingestellte Uhrzeit: {Uhrzeit}:00 Uhr"
                bot.sendMessage(telegramData.telegram_chat_id, message)  # and sends it

            if msg['text'] == 'LED off':
                led_pwm.stop()  # stop LED flashing
                led_pwm.ChangeDutyCycle(dutyCycle) #another initialization needed to make LED flashing work again
                led_pwm.ChangeFrequency(Frequency)

                message = f"Alarm wurde ausgestellt."
                bot.sendMessage(telegramData.telegram_chat_id, message)

def watchdog(start, ziel, hour, min):
    # function to keep an eye on the given train connection
    global watchdog_State,LED_STATE

    departure = str(hour) + str(min) # conversion from int to str necessary to be able to compare this string
                                     # with the departure string given by api
    if "S_ON" == watchdog_State:
        # calling api necessary to detect changes in timetable
        station_helper = StationHelper()
        station_helper.load_stations()
        found_stations_by_name = station_helper.find_stations_by_name(start)
        station = found_stations_by_name[0]

        timetable_helper = TimetableHelper(station=station, api_authentication=api)
        trains_at_given_hour = timetable_helper.get_timetable(hour)
        trains_with_changes = timetable_helper.get_timetable_changes(trains_at_given_hour)

        for i, train in enumerate(trains_with_changes): # cycling through trains and filtering by given information
            if ziel in train.stations:
                if departure in train.departure:  # identifying the train by planned time
                    if functions.delay(train) >= delayThreshhold:
                        message = f"Dein Zug um {functions.reverse_split(train.departure)[0:5]} Uhr von {start} nach " \
                                  f"{ziel} hat eine Verspätung von {functions.delay(train)} minuten.\n" \
                                  f"Die neue Abfahrtzeit ist {functions.reverse_split(train.train_changes.departure)[0:5]} Uhr."
                        bot.sendMessage(telegramData.telegram_chat_id, message)  # and sends it
                        watchdog_State = "S_OFF"

                        return 1    # delay got detected, watchdog turning off
        return 0


# initialize Telegram-Bot
bot = telepot.Bot(telegramData.telegram_bot_token)  # my bot is the bot with this token
bot.getMe()
bot.getUpdates()
MessageLoop(bot, handle_messages).run_as_thread() # message handle for  the telegram bot

# Endless loop to repeatedly check for train delay on given connection. If delay gets detected, LED will start flashing.
while 1:
    if(watchdog(meinBahnhof, zielBahnhof, hour, min)):
        led_pwm.start(50)

