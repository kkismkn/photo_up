from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

gauth = GoogleAuth()
gauth.CommandLineAuth()
drive = GoogleDrive(gauth)

def savePhotoToGoogle(image_url=None, image=None):
    f = drive.CreateFile({'title': 'test.jpg', 'mimeType': 'image/jpeg'})
    f.SetContentFile('test.jpg')
    f.Upload()
