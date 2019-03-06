# import configparser
from datetime import datetime, timedelta
import pytz
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

line_bot_api = LineBotApi('')
handler = WebhookHandler('')


def check_is_date(input):
    if input in ('今天', '明天', '後天', ):
        return True

    split_char = ''
    if '-' in input:
        split_char = '-'
    elif '/' in input:
        split_char = '/'
    else:
        pass

    try:
        if input.count(split_char) == 2:
            date_format = '%Y{split}%m{split}%d'.format(split=split_char)
        elif input.count(split_char) == 1:
            date_format = '%m{split}%d'.format(split=split_char)
        else:
            date_format = '%m%d'.format(split=split_char)

        datetime.strptime(input, date_format)
        return True

    except ValueError as err:
        return False

    return False


def get_date_str(date_input):
    fix_keywords = ('今天', '明天', '後天', )
    if date_input in fix_keywords:
        today = datetime.now(pytz.timezone('Asia/Taipei'))
        if date_input == '明天':
            today = today + timedelta(days=1)
        if date_input == '後天':
            today = today + timedelta(days=2)
        year = today.year
        month = today.month
        day = today.day
    else:
        split_char = ''
        if '-' in date_input:
            split_char = '-'
        elif '/' in date_input:
            split_char = '/'
        else:
            pass

        date_format_len = len(date_input.split(split_char))
        year = str(datetime.now().year) if date_format_len == 2 else date_input.split(split_char)[0]
        month = date_input.split(split_char)[0] if date_format_len == 2 else date_input.split(split_char)[1]
        day = date_input.split(split_char)[1] if date_format_len == 2 else date_input.split(split_char)[2]

    search_date = '{}-{}-{}'.format(year, '{:0>2}'.format(month), '{:0>2}'.format(day))

    return search_date


# @app.route("/tra", methods=['GET'])
def tra(command):
    from PtxAuth import Auth
    auth = Auth('', '')
    if len(command.split(' ')) < 2:
        notice_message = '查詢火車時刻表請輸入以下指令:\n'
        notice_message += '台鐵 [出發站] [抵達站] [日期] [時間]\n'
        notice_message += '例如\n'
        notice_message += '台鐵 臺北 臺東 10/19 12:00\n'
        notice_message += '台鐵 臺北 臺東 今天 18:00\n'
        notice_message += '台鐵 臺北 臺東 明天\n'
        notice_message += '台鐵 臺北 臺東 18:00\n'
        notice_message += '台鐵 臺北 臺東'
        return notice_message

    keywords = command.split(' ')

    origin = keywords[0]
    destination = keywords[1]

    if len(keywords) == 4:
        input_date = keywords[2]
        input_time = keywords[3]
    elif len(keywords) == 2:
        input_time = '00:00'
        input_date = '今天'
    else:
        is_date = check_is_date(keywords[2])
        if is_date:
            input_date = keywords[2]
            input_time = '00:00'
        else:
            input_time = keywords[2]
            input_date = '今天'

    query_station_name_url = "https://ptx.transportdata.tw/MOTC/v2/Rail/TRA/Station?$select=StationID&$filter=StationName/Zh_tw eq '{station}'&$format=JSON"

    response = requests.get(query_station_name_url.format(station=origin), headers=auth.get_auth_header())
    origin_station_id = json.loads(response.text)[0]['StationID']

    response = requests.get(query_station_name_url.format(station=destination), headers=auth.get_auth_header())
    destination_station_id = json.loads(response.text)[0]['StationID']

    search_date = get_date_str(input_date)
    print(search_date)

    url = """https://ptx.transportdata.tw/MOTC/v2/Rail/TRA/DailyTimetable/OD/{origin_station_id}/to/{destination_station_id}/{search_date}?$filter=OriginStopTime/DepartureTime gt '{search_time}'&$orderby=OriginStopTime/DepartureTime&$format=JSON"""

    url = url.format(origin_station_id=origin_station_id, destination_station_id=destination_station_id, search_date=search_date, search_time=input_time)

    response = requests.get(url, headers=auth.get_auth_header())

    train_records = json.loads(response.text)
    return_msg = ''

    return_msg += '{}<->{} {}\n'.format(origin, destination, search_date)
    return_template = "{} No:{: <4}\t{} - {}\n"
    for train_record in train_records:
        train_no = train_record['DailyTrainInfo']['TrainNo']
        train_type = train_record['DailyTrainInfo']['TrainTypeName']['Zh_tw']
        if '普悠瑪' in train_type:
            train_type = '普悠瑪'
        elif '太魯閣' in train_type:
            train_type = '太魯閣'
        elif '自強' in train_type:
            train_type = '自強號'
        elif '莒光' in train_type:
            train_type = '莒光號'

        # origin_stop = train_record['OriginStopTime']['StationName']['Zh_tw']
        departure_time = train_record['OriginStopTime']['DepartureTime']
        # destination_stop = train_record['DestinationStopTime']['StationName']['Zh_tw']
        arrival_time = train_record['DestinationStopTime']['ArrivalTime']
        return_msg += return_template.format(train_type, train_no, departure_time, arrival_time)

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

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))


if __name__ == "__main__":
    app.run(debug=True)
