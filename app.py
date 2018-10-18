import configparser
import requests
import json
from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

app = Flask(__name__)
# config = configparser.ConfigParser()
# config.read("config.ini")

# line_bot_api = LineBotApi(config['line_bot']['Channel_Access_Token'])
# handler = WebhookHandler(config['line_bot']['Channel_Secret'])

line_bot_api = LineBotApi('Access Token')
handler = WebhookHandler('Channel Secret')


def tra(command):
    from PtxAuth import Auth
    auth = Auth('APP ID', 'APP KEY')
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

    return_template = "{}-{} {} No:{} {}-{}\n"
    for train_record in train_records:
        train_no = train_record['DailyTrainInfo']['TrainNo']
        trin_type = train_record['DailyTrainInfo']['TrainTypeName']['Zh_tw']
        origin_stop = train_record['OriginStopTime']['StationName']['Zh_tw']
        departure_time = train_record['OriginStopTime']['DepartureTime']
        destination_stop = train_record['DestinationStopTime']['StationName']['Zh_tw']
        arrival_time = train_record['DestinationStopTime']['ArrivalTime']
        return_msg += return_template.format(origin_stop, destination_stop, trin_type, train_no, departure_time, arrival_time)

    return return_msg

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    tra_cmd = ('TRA', '台鐵', '臺鐵', '火車', )
    receive_cmd = event.message.text.split(' ')[0]
    detail_cmd = event.message.text.split(' ')[1:]
    if receive_cmd in tra_cmd:
        content = tra(' '.join(detail_cmd))
        print(len(content))
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0
    print(event.message.text)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))


if __name__ == "__main__":
    app.run(debug=True)
