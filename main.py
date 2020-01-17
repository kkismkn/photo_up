# -*- coding: utf-8 -*-


import os
import sys
import random
import datetime
import json
import requests
from PIL import Image
from io import BytesIO

#from argparse import ArgumentParser
from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
#使いたいイベントをインポート
from linebot.models import (
    ImageMessage,ImageSendMessage, MessageEvent, TextMessage, TextSendMessage
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
    if event.message.text == "アルバム":
        replyText = "https://drive.google.com/drive/folders/1Sa8RGDT2gVZYGRE_MIJ4_URlErRFBTKi"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=replyText)
        )
        return
    elif event.message.text == "新郎プロフィール":
        image_message = ImageSendMessage(
            original_content_url="https://drive.google.com/uc?export=view&id=12QV4uCPf01EmZHqniRXL_Q3Icmi6cioh",
            preview_image_url="https://drive.google.com/uc?export=view&id=12QV4uCPf01EmZHqniRXL_Q3Icmi6cioh",
        )
        # 13文字以上は改行が発生するので注意
        text_message = TextSendMessage(text='【生年月日】\n'
                     '　1991.04.25\n'
                     '【職業】\n'
                     '　製鉄所のシステム作る人\n'
                     '【趣味】\n'
                     '　酒ハンター、料理\n'
                     '【マイブーム】\n'
                     '　XXX\n'
                     '【マイブーム】\n'
                     '　XXX\n')
        line_bot_api.reply_message(event.reply_token, [image_message,text_message])
        return
    elif event.message.text == "新婦プロフィール":
        image_message = ImageSendMessage(
            original_content_url="https://drive.google.com/uc?export=view&id=1i4zZoykqBvAjSdABkY2O5R3_6pEpaTJ8",
            preview_image_url="https://drive.google.com/uc?export=view&id=1i4zZoykqBvAjSdABkY2O5R3_6pEpaTJ8",
        )
        text_message = TextSendMessage(text='【生年月日】\n'
                    '　1991.12.26\n'
                    '【職業】\n'
                    '　保険代理店の事務\n'
                    '【趣味】\n'
                    '　映画鑑賞\n'
                    '【マイブーム】\n'
                    '　\n')
        line_bot_api.reply_message(event.reply_token, [image_message,text_message])
        return
    else:
        replyList = ["写真を…\n写真をください…", "写真をくれればクラウドに保存するよ！", "なんや", "はろー", "会話は…ちょっと…",
                "わたしがくまだ", "はちみつください", "鮭とかくれてもいいよ"]
        replyText = random.choice(replyList)

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=replyText)
        )

#画像メッセージ受信時の挙動をハンドラへ設定
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    #ファイルをサーバ(Heroku)へ一時保存
    message_id = event.message.id
    file_name = save_image(message_id)

    #GoogleDriveへアップロード
    save_to_google(file_name, message_id, '195Q4Ngwglfd0XDOcMxQ6ruz4ccHHig-p')#個人フォルダ
    save_to_google(file_name, message_id, '1Sa8RGDT2gVZYGRE_MIJ4_URlErRFBTKi')#公開フォルダ

    #一時保存したファイルを削除
    os.remove(file_name)

    #ユーザへ応答
    #replyList = ["いい写真！", "あー、これは…！", "さすがですねぇ！", "素晴らしい！", "もっともっと！", "ありがとう！", "神"]
    #replyText = random.choice(replyList)
    #line_bot_api.reply_message(
    #event.reply_token,
    #TextSendMessage(text=replyText)
    #)


#GoogleDriveへ画像を保存する
def save_to_google(file_name, message_id, folder_pass):
    #現在時刻取得(サーバ時刻 + 9時間)
    now = datetime.datetime.now() + datetime.timedelta(hours = 9)

    #ファイルのガラを生成
    #ファイル名：YYYYMMDDhh24mmss-ファイル名(メッセージID)
    #形式：jpg
    f = drive.CreateFile({'title': now.strftime("%Y%m%d%H%M%S") + '-' + message_id,
                          'mimeType': 'image/jpeg',
                          'parents': [{'kind': 'drive#fileLink', 'id':folder_pass}]})

    #ファイルアップロード
    f.SetContentFile(file_name)
    f.Upload()


#メッセージIDに紐づく画像をサーバ(Heroku)へ一時保存
#戻り値：保存したファイル名(絶対パス)
def save_image(messege_id):
    message_content = line_bot_api.get_message_content(messege_id)
    image = Image.open(BytesIO(message_content.content))
    file_name = '/tmp/' + messege_id + '.jpg'
    image.save(file_name)

    return file_name

# 新婦画像送信用
def make_image_message():
    messages = ImageSendMessage(
        original_content_url="https://hogehoge.jpg", #JPEG 最大画像サイズ：240×240 最大ファイルサイズ：1MB(注意:仕様が変わっていた)
        preview_image_url="https://hogehoge-mini.jpg" #JPEG 最大画像サイズ：1024×1024 最大ファイルサイズ：1MB(注意:仕様が変わっていた)
    )
    return messages

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
