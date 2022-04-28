import requests
import sys
import jwt, base64, json
from pywidevine.decrypt.wvdecrypt import WvDecrypt

# fuck aha
contentID = input("Enter Content ID: ")
authorization = 'value of account specific authorization header'
x_authorization = 'value of account specific x-authorization header'
deviceID = 'c2abeefd-5997-4f36-bacb-276760c1a39b' # chrome deviceID, constant
headers = {
    'authority': 'device-register-service.api.aha.firstlight.ai',
    'authorization': authorization,
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36',
    'x-client-id': 'firstlight-main-iosmobile',
    'x-authorization': auth,
}
response = requests.post(url= 'https://device-register-service.api.aha.firstlight.ai/device/app/register', headers= headers, data=
'{"uniqueId":"' + deviceID + '"}'
)

# print (response.content)

secret = json.loads(response.content)['data']['secret']
servertime = int(json.loads(response.content)['header']['system_time'])
jwttime = (servertime)/1000
x = jwt.encode({
  "deviceId": deviceID,
  "aud": "playback-auth-service",
  "iat": jwttime,
  "exp": jwttime + 30
}, base64.b64decode(secret), algorithm="HS256")

json_data = {
    'deviceName': 'mobileweb',
    'deviceId': deviceID,
    'contentId': contentID,
    'contentTypeId': 'vod',
    'catalogType': 'movie',
    'mediaFormat': 'dash',
    'drm': 'widevine',
    'delivery': 'streaming',
    'disableSsai': 'false',
    'deviceManufacturer': 'mobile-web',
    'deviceModelName': 'web',
    'deviceModelNumber': 'chrome',
    'deviceOs': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36',
    'deviceToken': x}

headers2 = {
    'authority': 'playback-auth-service.api.aha.firstlight.ai',
    'authorization': authorization,
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36',
    'x-client-id': 'firstlight-main-iosmobile',
    'x-authorization': x_authorization,
    'x-device-id': x,
}
response2 = requests.post('https://playback-auth-service.api.aha.firstlight.ai/media/content/authorize', headers=headers2, json=json_data)
try:
    mpd_url = json.loads(response2.content)['data']['contentUrl']
    license_url = json.loads(response2.content)['data']['licenseUrl']
except KeyError:
    print("Invalid Content ID!")
    sys.exit()


print('MPD URL is ' + mpd_url)
print('Requesting License..')

wvdecrypt = WvDecrypt('AAAAXHBzc2gAAAAA7e+LqXnWSs6jyCfc1R0h7QAAADwIARIQrlh/qvWWR1CGNZFfHVQ+VRoIdXNwLWNlbmMiGHJsaC9xdldXUjFDR05aRmZIVlErVlE9PSoAMgA=') #constant PSSH for all titles
chal = wvdecrypt.get_challenge()
response = requests.post(url=license_url, data=chal, headers = {
    'authority': 'widevine-proxy.api.aha.firstlight.ai',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36',
})
license = base64.b64encode(response.content)
wvdecrypt.update_license(license)
keys = wvdecrypt.start_process()
print("Obtained Keys!")
for key in keys:
        if key.type == 'CONTENT':
            key = ('{}:{}'.format(key.kid.hex(), key.key.hex()))
            print (key)
