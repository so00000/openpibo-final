import os
import sys
import base64
import time
import cv2
sys.path.append("/home/pi/openpibo-final/lib")
from pibo_control import Pibo_Control

from flask import Flask, render_template
from flask_socketio import SocketIO
from vision.stream import VideoStream

from device.devicelib import cDevice
from threading import Thread

device = cDevice()
app = Flask(__name__)
socketio = SocketIO(app)

offair = False
img = ""

@app.route('/')
def sessions():
  return render_template('index.html')

@app.route('/test')
def test():
  return render_template('base.html')
  
@app.route('/calendar')
def calendar():
  return render_template('calendar.html')

@app.route('/weather')
def weather():
  return render_template('weather.html')

@app.route('/news')
def news():
  return render_template('news.html')

@app.route('/camera')
def camera():
  return render_template('camera.html')

@app.route('/control')
def control():
  return render_template('control.html')

@app.route('/translate')
def translate():
  return render_template('translate.html')

#def messageReceived(methods=['GET', 'POST']):
#    print()

def start_streaming():
  global offair, img
  offair = False
  vs = VideoStream().start()
  while True:
    if offair:
      img = stop_img
      vs.stop()
      break
    img = vs.read()
    img = cv2.imencode('.jpg', img)[1].tobytes()
    img = base64.b64encode(img).decode('utf-8')
    stop_img = img
    socketio.emit('result', '동영상 촬영을 시작합니다.')
    socketio.emit('img', img)
    time.sleep(0.1)

@socketio.on('command')
def f_command(command, methods=['GET', 'POST']):
  global offair, img
  ret = pibo.decode_func(command)
  if "사진" in command:
    img = base64.b64encode(open('/home/pi/openpibo-final/images/photo.jpg', 'rb').read()).decode('utf-8')
  elif "그만" in command:
    offair = True
    time.sleep(0.5)
    socketio.emit('result', ret)
  elif "동영상" in command:
    t = Thread(target=start_streaming, args=())
    t.daemon = True
    t.start()
    # t.join()
  else:
    img = base64.b64encode(open('/home/pi/openpibo-final/images/background.png', 'rb').read()).decode('utf-8')
  socketio.emit('result', ret)
  socketio.emit('img', img)

@socketio.on('voice')
def voice_cmd():
  pibo.check_device('voice')

def check_voice():
  global offair, img
  while True:
    if pibo.control_voice == True:
      if len(pibo.voice_answer) != 0:
        print('voice_cmd in main', pibo.voice_cmd)
        if "사진" in pibo.voice_cmd:
          img = base64.b64encode(open('/home/pi/openpibo-final/images/photo.jpg', 'rb').read()).decode('utf-8')
        elif "그만" in pibo.voice_cmd:
          offair = True
          time.sleep(0.5)
          socketio.emit('result', pibo.voice_answer.pop(0))
          pibo.control_voice = False
        elif "동영상" in pibo.voice_cmd:
          t2 = Thread(target=start_streaming, args=())
          t2.daemon = True
          t2.start()
          # t2.join()
        else:
          img = base64.b64encode(open('/home/pi/openpibo-final/images/background.png', 'rb').read()).decode('utf-8')
        socketio.emit('voice_cmd', pibo.voice_cmd)
        socketio.emit('result', pibo.voice_answer.pop(0))
        socketio.emit('img', img)
        pibo.control_voice = False
      else:
        socketio.emit('result', pibo.voice_answer.pop(0))
      

if __name__ == '__main__':
  pibo = Pibo_Control()
  v = Thread(target=check_voice, args=())
  v.start()
  socketio.run(app, host='0.0.0.0', port=8888, debug=False)
