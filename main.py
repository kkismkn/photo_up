# -*- coding: utf-8 -*-


import os
import sys
import datetime
import random
from PIL import Image
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

#google認証
gauth = GoogleAuth()
gauth.CommandLineAuth()
drive = GoogleDrive(gauth)

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
    replyList = ["写真を…写真をください…", "写真をくれればクラウドに保存するよ！", "なんや", "はろー", "会話は…ちょっと…",
                     "わたしがくまだ", "はちみつください", "鮭とかくれてもいいよ"]
    replyText = random.choice(replyList)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=replyText)
    )

#画像メッセージ受診時の挙動をハンドラへ設定
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    #ファイルのガラを生成
    #ファイル名：YYYYMMDDhh24mmssfff
    #形式：jpg
    f = drive.CreateFile({'title': datetime.datetime.now().strftime('%Y%m%d%H%M%S%f'),
                          'mimeType': 'image/jpeg',
                          'parents': [{'kind': 'drive#fileLink', 'id':'195Q4Ngwglfd0XDOcMxQ6ruz4ccHHig-p'}]}) #通常用
                          #'parents': [{'kind': 'drive#fileLink', 'id':'1Sa8RGDT2gVZYGRE_MIJ4_URlErRFBTKi'}]}) #結婚式用

    #ファイルをサーバへ保存
    message_id = event.message.id
    filename = save_image(message_id)

    #ファイルアップロード
    f.SetContentFile(filename)
    f.Upload()

    #ユーザへ応答
    replyList = ["いい写真！", "あー、これは…！", "さすがですねぇ！", "素晴らしい！", "もっともっと！", "ありがとう！", "神"]
    replyText = random.choice(replyList)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=replyText)
    )


#メッセージIDに紐づく画像をサーバへ保存
#戻り値：保存したファイル名(絶対パス)
def save_image(messegeid):
    message_content = line_bot_api.get_message_content(messegeid)
    image = Image.open(BytesIO(message_content.content))
    filename = '/tmp/' + messegeid + '.jpg'
    image.save(filename)

    return filename


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
