# coding=utf-8
import json
import requests
from PtxAuth import Auth
import pandas as pd

auth = Auth('c6751135db984d388b28508a966e573d', 's8_o4xquB3baymoNwjPVwRRfm_s')

command = '鶯歌 內壢 2018-10-18'

origin, destination, search_date = command.split(' ')

query_station_name_url = "https://ptx.transportdata.tw/MOTC/v2/Rail/TRA/Station?$select=StationID&$filter=StationName/Zh_tw eq '{station}'&$format=JSON"

response = requests.get(query_station_name_url.format(station=origin), headers=auth.get_auth_header())
origin_station_id = json.loads(response.text)[0]['StationID']

response = requests.get(query_station_name_url.format(station=destination), headers=auth.get_auth_header())
destination_station_id = json.loads(response.text)[0]['StationID']

url = 'https://ptx.transportdata.tw/MOTC/v2/Rail/TRA/DailyTimetable/OD/{origin_station_id}/to/{destination_station_id}/{search_date}?$orderby=OriginStopTime/DepartureTime&$format=JSON'

url = url.format(origin_station_id=origin_station_id, destination_station_id=destination_station_id, search_date=search_date)

response = requests.get(url, headers=auth.get_auth_header())

train_records = json.loads(response.text)
return_msg = ''

return_template = "{}<->{} {} No:{} {} - {}\n"
for train_record in train_records:
    train_no = train_record['DailyTrainInfo']['TrainNo']
    trin_type = train_record['DailyTrainInfo']['TrainTypeName']['Zh_tw']
    origin_stop = train_record['OriginStopTime']['StationName']['Zh_tw']
    departure_time = train_record['OriginStopTime']['DepartureTime']
    destination_stop = train_record['DestinationStopTime']['StationName']['Zh_tw']
    arrival_time = train_record['DestinationStopTime']['ArrivalTime']
    return_msg += return_template.format(origin_stop, destination_stop, trin_type, train_no, departure_time, arrival_time)

print(return_msg)