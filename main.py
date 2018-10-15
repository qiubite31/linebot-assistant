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

line_bot_api = LineBotApi('os/EeO0Jt4N8td2KJywVKoWnIBZZImbtW7gDw4yi1ReE3AOHeobz25oW2+XGCvoqceUEVVfl4sg647cQAHEJuUkuss2ISTqEIBI8m2xdENSbKX/qq9mZzcaYWpwAVIlz2z1StfhY/rAI6R/6cA/h+gdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('9c4ba64d8f9cb71af6b6ff9f22137ea9')


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
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))


if __name__ == "__main__":
    app.run()
