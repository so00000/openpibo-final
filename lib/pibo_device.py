import sys, time, datetime
from utils.config import Config as cfg
sys.path.append(cfg.OPENPIBO_PATH + '/lib')

from speech.speechlib import cSpeech
from speech.speechlib import cDialog
from audio.audiolib import cAudio
from oled.oledlib import cOled
from motion.motionlib import cMotion
from device.devicelib import cDevice
from vision.visionlib import cCamera
from vision.visionlib import cFace
from vision.visionlib import cDetect

import pibo_extend
from threading import Thread, Lock

device_voice = False

class Pibo_Device:
  def __init__(self, func=None):
    self.play_filename = '/home/pi/openpibo-final/data/tts.mp3'
    self.D = cDialog(conf=cfg)
    self.A = cAudio()
    self.O = cOled(conf=cfg)
    self.M = cMotion(conf=cfg)
    self.CA = cCamera()
    self.FA = cFace(conf=cfg)
    self.DT = cDetect(conf=cfg)
    self.T = cSpeech(conf=cfg)
    self.H = cDevice()
    self.H.send_cmd(self.H.code['VERSION'])
    self.H.send_cmd(self.H.code['PIR'], "on")
    self.display_oled('/home/pi/openpibo-final/bot_icon/pibo_logo_b.png')
    self.next_cmd = [False, ""]
    self.func = func
    t = Thread(target=self.update, args=())
    t.daemon = True
    t.start()
    self.pe = pibo_extend
    self.check_charge = False
    self.welcome()

  def update(self):
    self.system_check_time = time.time()
    self.battery_check_time = time.time()

    while True:
      if self.next_cmd[0] == True:
        data = self.H.send_raw(self.next_cmd[1])
        self.func(data)

      if time.time() - self.system_check_time > 1:  # 시스템 메시지 1초 간격 전송
        data = self.H.send_cmd(self.H.code['SYSTEM'])
        self.func(data)
        self.system_check_time = time.time()

      if time.time() - self.battery_check_time > 10: # 배터리 메시지 10초 간격 전송
        data = self.H.send_cmd(self.H.code['BATTERY'])
        idx = data.find(':')
        charge = data[idx+1:-1]
        if int(charge) <= 20:
          if self.check_charge == False:
            for i in range(5):
              self.H.send_raw("#20:255,0,0!")
              time.sleep(0.5)
              self.H.send_raw("#20:0,0,0!")
            self.speak('<speak>배터리가 {}% 남았어요. 충전이 필요합니다.</speak>'.format(int(charge)))
            self.check_charge = True
        self.func(data)
        self.battery_check_time = time.time()
      time.sleep(0.1)

  def display_oled(self, filename):
    self.O.draw_image(filename)
    self.O.show()

  def listen(self, lang='ko-KR'):
    return self.T.stt(lang=lang)

  def speak(self, string):
    self.T.tts(string, self.play_filename)
    self.A.play(self.play_filename, volume=-1500)

  def picture(self, string, voice=False):
    img = self.CA.read()
    ret_img = img.copy()

    datas = self.FA.detect(img)
    for data in datas:
      x,y,w,h = data
      self.CA.rectangle(ret_img, (x,y), (x+w,y+h), color=(30,128,30), tickness=2)

    datas = self.DT.detect_object(img)
    for data in datas:
      x1,y1,x2,y2 = data["position"]
      label = "{}: {:.2f}%".format(data["name"], data["score"])
      self.CA.rectangle(ret_img, (x1,y1), (x2,y2), color=(30,30,128), tickness=2)
      self.CA.putText(ret_img, label, (x1+15, y1+15), size=0.5, color=(128,30,30), tickness=2)

    self.CA.imwrite('/home/pi/openpibo-final/images/photo.jpg', ret_img)
    return "사진촬영했어요"

  def analyze_sentence(self, string):
    return self.D.mecab_pos(string)

  def chat(self, string):
    return self.D.get_dialog(string)

  def motion(self, key):
    self.M.set_motion(key)
    return "움직였어. "

  def welcome(self):
    now = datetime.datetime.now()
    nowTime = now.strftime('%H:%M')
    idx = nowTime.find(':')
    hour = nowTime[:idx]
    hour = int(hour)

    if 8 <= hour <= 12:
      greeting_ment = '오전'
    elif 12 < hour <= 18:
      greeting_ment = '오후'
    else:
      greeting_ment = '저녁'
    
    return_cal = self.pe.calendar_bot("오늘 일정 알려줘")

    cal_idx = return_cal.find(',')
    notice_cal = return_cal[cal_idx+1:]
    if '없어요' in notice_cal:
      self.speak('<speak>안녕. '+greeting_ment+'</speak>')
      self.motion('greeting')
      return
    self.speak('<speak>오늘 ' + notice_cal + ' 일정이 있어요. </speak>')
    self.motion('greeting')

  def translate(self, string, voice=False):
    if voice == True:
      return self.no_voice()
    ret = "영어 또는 한국어 번역만 지원합니다."
    if '영어' not in string and '한국어' not in string:
      return ret
  
    lang = 'en' if '영어' in string else 'ko'
    if '[' not in string or ']' not in string:
      ret = '잘못된 형식입니다. [] 안에 번역할 문장을 넣어주세요.'
      return ret
    for i in range(len(string)):
      if string[i] == '[':
        start_idx = i+1
      elif string[i] == ']':
        end_idx = i
    sentence = string[start_idx:end_idx]
    return self.T.translate(sentence, lang)

  def eye(self, string, voice=False):
    ret = "목록에 없는 색상입니다."
    color_list = {
      '검정색': (0,0,0),
      '흰색': (255,255,255),
      '빨간색': (255,0,0),
      '주황색': (200,75,0),
      '노란색': (255,255,0),
      '초록색': (0,255,0),
      '하늘색': (0,255,255),
      '파란색': (0,0,255),
      '보라색': (255,0,255),
      '분홍색': (255,51,153),
    }
    if '꺼줘' in string:
      self.H.send_raw("#20:0,0,0!")
      ret = "껐어요."
      return ret
    else:
      for key in color_list.keys():
        if key in string:
          ret = "{} 눈 켰어요.".format(key)
          color = color_list[key]
          self.H.send_raw("#20:{}!".format(",".join(str(p) for p in color)))
          return ret
    return ret

  def detect(self, string, voice=False):
    img = self.CA.read()
    obj = self.DT.detect_object(img)
    qr = self.DT.detect_qr(img)
    text = self.DT.detect_text(img)
    return "인식 완료"
  
  def no_voice(self):
    return "해당 기능은 음성 모드를 지원하지 않습니다."

  # def video(self):
  #   while True:
  #     if offair:
  #       break
  #     img = self.CA.read()
  #     self.CA.imwrite('/home/pi/openpibo-final/images/video.jpg', img)
  #   return img

  