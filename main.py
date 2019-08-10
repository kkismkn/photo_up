# -*- coding: utf-8 -*-


import os
import sys
import datetime

from io import BytesIO
from argparse import ArgumentParser
from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
#使いたいイベントをインポート
from linebot.models import (
    ImageMessage, MessageEvent, TextMessage, TextSendMessage
)
#googleAPI
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)


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

#テキストメッセージ受信時の挙動をハンドラへ設定
@handler.add(MessageEvent, message=TextMessage)
#オウム返し
def message_text(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="なんや")
    )

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    #google認証
    gauth = GoogleAuth()
    gauth.CommandLineAuth()
    drive = GoogleDrive(gauth)

    #ファイルのガラを生成
    #ファイル名：YYYYMMDDhh24mmss
    #形式：jpg
    f = drive.CreateFile({'title': datetime.datetime.now().strftime('%Y%m%d%H%M%S%N'), 'mimeType': 'image/jpeg'})

    message_id = event.message.id
    filename = save_image(message_id)

    #ファイルアップロード
    f.SetContentFile(filename)

    f.Upload()

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="いい写真")
    )

#メッセージIDに紐づく画像をサーバへ保存
#戻り値：保存したファイル名(絶対パス)
def save_image(messegeid):
    message_content = line_bot_api.get_message_content(messegeid)

    i = Image.open(BytesIO(message_content.content))
    filename = '/tmp/' + messegeid + '.jpg'
    i.save(filename)

    return filename


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
