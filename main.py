import time
import json
from deutsche_bahn_api.api_authentication import ApiAuthentication
from deutsche_bahn_api.station_helper import StationHelper
from deutsche_bahn_api.timetable_helper import TimetableHelper
import telepot
from telepot.loop import MessageLoop

api = ApiAuthentication("4d92b50e16b9e7a97f9a95d55a08570e", "3ac2ae0cd903b5aa9315ebf338addbaf")
success: bool = api.test_credentials()

station_helper = StationHelper()
station_helper.load_stations()
# found_stations = station_helper.find_stations_by_lat_long(47.996713, 7.842174, 10)
found_stations_by_name = station_helper.find_stations_by_name("Hamburg Hbf")
station = found_stations_by_name[0]

timetable_helper = TimetableHelper(station=station, api_authentication=api)
trains_in_this_hour = timetable_helper.get_timetable()
# trains_at_given_hour = timetable_helper.get_timetable(12)

trains_with_changes = timetable_helper.get_timetable_changes(trains_in_this_hour)

# Hier gehts los mit der Sortierung
metronometrains = [train for train in trains_in_this_hour if
                   train.train_type == "ME"]  # sortiere  die Liste nach dem Zugtyp Metronom
Delayed_metronom_trains_LG_to_HH = [train for train in metronometrains if
                                    train.stations == "Winsen(Luhe)|Hamburg-Harburg|Hamburg Hbf"]  # sortiere Liste von Metronom Zügen nach Zielbahnhof
print(trains_with_changes)

# hallo hallo hallo

# Erster Kommentar vom GITGott Lukas

# Hier erfolgt eine Ausgabe auf der Konsole
print("Delayed Metronom Trains from Lüneburg to Hamburg:")
for i, train in enumerate(Delayed_metronom_trains_LG_to_HH):
    print(f"{i} = {train}")
    print(f"  departure = {train.departure}")
    print(f"  platform = {train.platform}")
    print(f"  stations = {train.stations}")
    print(f"  stop_id = {train.stop_id}")
    print(f"  train_changes = {train.train_changes}")
    print(f"  train_line = {train.train_line}")
    print(f"  train_number = {train.train_number}")
    print(f"  train_type = {train.train_type}")
    print(f"  trip_type = {train.trip_type}")

# Telegram Teil Update
# Token des Telegram-Bots
telegram_bot_token = '6021930981:AAFhsTB6Ahe7MXtCh6R20EnyltWi_Q10MZs'

# Chat-ID des Empfängers - Lukas Bot aktuell
telegram_chat_id = '6235783485'


def handle_messages(msg):
    content_type, chat_type, chat_id = telepot.glance(
        msg)  # Python-Telegram function that returns the values message type, chat type  and chat id from a telegram message
    if content_type == 'text':  # glance checks the message type. If the type is in the form of text, we have a valid message
        if msg['text'] == 'Züge':  # user input
            for i, train in enumerate(trains_in_this_hour):
                print(f"{i} = {train}")
                print(f"  departure = {train.departure}")
                print(f"  platform = {train.platform}")
                print(f"  stations = {train.stations}")
                print(f"  stop_id = {train.stop_id}")
                print(f"  train_changes = {train.train_changes}")
                print(f"  train_line = {train.train_line}")
                print(f"  train_number = {train.train_number}")
                print(f"  train_type = {train.train_type}")
                print(f"  trip_type = {train.trip_type}")

        if msg['text'] == 'Moin':  # user is kind
            message = f"Menü: 1. Züge"  # bot prepares a welcoming message
            bot.sendMessage(telegram_chat_id, message)  # and sends it


# initialize Telegram-Bot
bot = telepot.Bot(telegram_bot_token)  # my bot is the bot with this token
bot.getMe()
bot.getUpdates()

# message handle for  the telegram bot
MessageLoop(bot, handle_messages).run_as_thread()

while 1:
    time.sleep(10)
