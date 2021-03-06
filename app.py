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


def check_input_is_train_type(input):
    if '自強' in input:
        return True
    elif '對號' in input:
        return True
    elif '區間' in input:
        return True
    elif '莒光' in input:
        return True
    elif '太魯閣' in input:
        return True
    elif '普悠瑪' in input:
        return True
    else:
        return False

def check_train_type(target_type, given_type):
    if '自強' in target_type and given_type in ('自強號', '太魯閣', '普悠瑪',):
        return True
    elif '對號' in target_type and given_type in ('自強號', '太魯閣', '普悠瑪', '莒光號', ):
        return True
    elif '區間' in target_type and '區間' in given_type:
        return True
    elif '莒光' in target_type and '莒光' in given_type:
        return True
    elif '太魯閣' == target_type and '太魯閣' == given_type:
        return True
    elif '普悠瑪' == target_type and '普悠瑪' == given_type:
        return True
    else:
        return False


def get_current_time():
    curr_dt = datetime.now(pytz.timezone('Asia/Taipei'))
    return '{}:{:0>2}'.format(curr_dt.hour, curr_dt.minute)


def default_msg():
    notice_message = '查詢火車時刻表請輸入以下指令:\n'
    notice_message += '台鐵 [出發站] [抵達站] [日期] [時間] [車種]\n'
    notice_message += '例如\n'
    notice_message += '台鐵 臺北 臺東 10/19 12:00\n'
    notice_message += '台鐵 臺北 臺東 今天 18:00\n'
    notice_message += '台鐵 臺北 臺東 明天\n'
    notice_message += '台鐵 臺北 臺東 18:00\n'
    notice_message += '台鐵 臺北 臺東 自強\n'
    notice_message += '台鐵 臺北 臺東 明天 自強\n'
    notice_message += '台鐵 臺北 臺東 19:00 自強\n'
    notice_message += '台鐵 臺北 臺東'
    return notice_message


# @app.route("/tra", methods=['GET'])
def tra(command):
    from PtxAuth import Auth
    auth = Auth('', '')
    if len(command.split(' ')) < 2:
        return default_msg()

    keywords = command.split(' ')

    origin = keywords[0].replace('台', '臺')
    destination = keywords[1].replace('台', '臺')

    if len(keywords) == 2:
        input_time = get_current_time()
        input_date = '今天'
        filter_train_type = None
    elif len(keywords) == 3:
        is_date = check_is_date(keywords[2])
        is_train_type = check_input_is_train_type(keywords[2])

        if is_date:
            input_date = keywords[2]
            input_time = get_current_time()
            filter_train_type = None
        elif is_train_type:
            input_time = get_current_time()
            input_date = '今天'
            filter_train_type = keywords[2]
        else:
            input_date = '今天'
            input_time = keywords[2]
            filter_train_type = None
    elif len(keywords) == 4:
        is_parm2_date = check_is_date(keywords[2])
        is_parm3_train_type = check_input_is_train_type(keywords[3])

        if is_parm2_date:
            input_date = keywords[2]
            input_time = keywords[3] if not is_parm3_train_type else '00:00'
            filter_train_type = keywords[3] if is_parm3_train_type else None
        else:
            input_date = '今天'
            input_time = keywords[2]
            filter_train_type = keywords[3]
    elif len(keywords) == 5:
        input_date = keywords[2]
        input_time = keywords[3]
        filter_train_type = keywords[4]
    else:
        pass

    query_station_name_url = "https://ptx.transportdata.tw/MOTC/v2/Rail/TRA/Station?$select=StationID&$filter=StationName/Zh_tw eq '{station}'&$format=JSON"

    response = requests.get(query_station_name_url.format(station=origin), headers=auth.get_auth_header())
    origin_station_id = json.loads(response.text)[0]['StationID']

    response = requests.get(query_station_name_url.format(station=destination), headers=auth.get_auth_header())
    destination_station_id = json.loads(response.text)[0]['StationID']

    search_date = get_date_str(input_date)

    url = """https://ptx.transportdata.tw/MOTC/v2/Rail/TRA/DailyTimetable/OD/{origin_station_id}/to/{destination_station_id}/{search_date}?$filter=OriginStopTime/DepartureTime gt '{search_time}'&$orderby=OriginStopTime/DepartureTime&$format=JSON"""
    url = url.format(origin_station_id=origin_station_id, destination_station_id=destination_station_id, search_date=search_date, search_time=input_time)
    response = requests.get(url, headers=auth.get_auth_header())
    train_records = json.loads(response.text)


    url = """https://ptx.transportdata.tw/MOTC/v2/Rail/TRA/LiveBoard/Station/{origin_station_id}?$top=30&$format=JSON"""
    url = url.format(origin_station_id=origin_station_id)
    response = requests.get(url, headers=auth.get_auth_header())
    train_status_records = json.loads(response.text)
    train_to_delaytime = {x['TrainNo']: x['DelayTime'] for x in train_status_records}

    return_msg = ''

    return_msg += '{}<->{} {}\n'.format(origin, destination, search_date)
    return_template = "{} No:{: <4}\t{} - {}+{}\n"

    count = 0
    for train_record in train_records:
        train_no = train_record['DailyTrainInfo']['TrainNo']
        train_type = train_record['DailyTrainInfo']['TrainTypeName']['Zh_tw']
        delaytime = train_to_delaytime.get(train_no, 0)

        if '普悠瑪' in train_type:
            train_type = '普悠瑪'
        elif '太魯閣' in train_type:
            train_type = '太魯閣'
        elif '自強' in train_type:
            train_type = '自強號'
        elif '莒光' in train_type:
            train_type = '莒光號'

        if filter_train_type:
            is_select_train_type = check_train_type(filter_train_type, train_type)
            if not is_select_train_type:
                continue

        # origin_stop = train_record['OriginStopTime']['StationName']['Zh_tw']
        departure_time = train_record['OriginStopTime']['DepartureTime']
        # destination_stop = train_record['DestinationStopTime']['StationName']['Zh_tw']
        arrival_time = train_record['DestinationStopTime']['ArrivalTime']
        return_msg += return_template.format(train_type, train_no, departure_time, arrival_time, delaytime)

        count += 1
        if count == 20:
            break

    return return_msg


def metro(command):
    from PtxAuth import Auth
    auth = Auth('', '')
    if len(command.split(' ')) < 2:
        return default_msg()

    keywords = command.split(' ')

    origin = keywords[0]
    destination = keywords[1]

    url = "https://ptx.transportdata.tw/MOTC/v2/Rail/Metro/ODFare/TRTC?$filter=OriginStationName/Zh_tw eq '{origin_station_name}' and DestinationStationName/Zh_tw eq '{destination_station_name}'&$top=30&$format=JSON"

    url = url.format(origin_station_name=origin, destination_station_name=destination)

    response = requests.get(url, headers=auth.get_auth_header())

    fare_records = json.loads(response.text)[0]

    destination_station_id = fare_records['DestinationStationID']
    origin_station_id = fare_records['OriginStationID']

    fare_adult = fare_records['Fares'][0]['Price']
    fare_adult_eticket = fare_records['Fares'][9]['Price']

    msg = "{}到{}票價{}電子票價{}".format(origin, destination, fare_adult, fare_adult_eticket)

    return msg

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
    receive_text = event.message.text.split(' ')
    receive_cmd = event.message.text.split(' ')[0]
    detail_cmd = event.message.text.split(' ')[1:]

    if receive_cmd == '捷運':
        input_cmd = ' '.join(detail_cmd)
        content = metro(input_cmd)
    else:

        if receive_cmd in tra_cmd:
            input_cmd = ' '.join(detail_cmd)
        else:
            input_cmd = 'TRA'

        content = tra(input_cmd)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=content))
    return 0


if __name__ == "__main__":
    app.run(debug=True)
