
import json
from deutsche_bahn_api.api_authentication import ApiAuthentication
from deutsche_bahn_api.station_helper import StationHelper
from deutsche_bahn_api.timetable_helper import TimetableHelper

api = ApiAuthentication("ID", "SECRET")
success: bool = api.test_credentials()

station_helper = StationHelper()
station_helper.load_stations()
# found_stations = station_helper.find_stations_by_lat_long(47.996713, 7.842174, 10)
found_stations_by_name = station_helper.find_stations_by_name("Lüneburg")
station = found_stations_by_name[0]

timetable_helper = TimetableHelper(station=station, api_authentication=api)
trains_in_this_hour = timetable_helper.get_timetable()
# trains_at_given_hour = timetable_helper.get_timetable(12)

trains_with_changes = timetable_helper.get_timetable_changes(trains_in_this_hour)

# Hier gehts los mit der Sortierung
metronometrains = [train for train in trains_in_this_hour if train.train_type == "ME"] #sortiere  die Liste nach dem Zugtyp Metronom
Delayed_metronom_trains_LG_to_HH = [train for train in metronometrains if
                                    train.stations == "Winsen(Luhe)|Hamburg-Harburg|Hamburg Hbf"]   #sortiere Liste von Metronom Zügen nach Zielbahnhof
print(trains_with_changes)

# hallo hallo hallo

#Erster Kommentar vom GITGott Lukas

