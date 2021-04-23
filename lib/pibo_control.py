import sys
sys.path.append("/home/pi/openpibo-final/lib")

from pibo_device import Pibo_Device
import pibo_extend as pe

motion_db = {
  "앞":"forward1",
  "앞쪽":"forward1",
  "뒤":"backward1",
  "뒤쪽":"backward1",
  "왼쪽":"left",
  "오른쪽":"right",
}


class Pibo_Control:
  def __init__(self):
    self.pd = Pibo_Device(func=self.check_device)
    self.bot_db = {
      "날씨": pe.weather_bot,
      "미세먼지": pe.weather_bot,
      "뉴스": pe.news_bot,
      "일정" : pe.calendar_bot,
      "사진" : self.pd.picture,
      "번역" : self.pd.translate,
      "눈" : self.pd.eye,
      "인식" : self.pd.detect,
    }
    self.control_voice = False
    self.voice_cmd = ''
    self.voice_answer = []
  
  def check_device(self, s):
    arr = s.split(':')
    if s == 'voice':
      self.pd.display_oled('/home/pi/openpibo-final/bot_icon/pibo_hear.png')
      ret = self.pd.listen(lang='ko-KR')
      if len(ret) > 0:
        self.decode_func(ret, voice=True)
        self.pd.display_oled('/home/pi/openpibo-final/bot_icon/pibo_logo_b.png')

    elif 'touch' in arr[1]:
      self.pd.display_oled('/home/pi/openpibo-final/bot_icon/pibo_hear.png')
      ret = self.pd.listen(lang='ko-KR')
      if len(ret) > 0:
        self.decode_func(ret, voice=True)
        self.pd.display_oled('/home/pi/openpibo-final/bot_icon/pibo_logo_b.png')

  def decode_func(self, string ="오늘 날씨 알려줘", voice=False):
    global control_voice
    matched, answer = False, ''
    items = self.pd.analyze_sentence(string)
    if voice == True:
      self.control_voice = True
      self.voice_cmd = string
    else:
      self.control_voice = False
    
    for item in items:
      if item[0] == '동영상' or item[0] == '그만':
        if item[0] == '동영상':
          answer = '동영상 촬영을 시작합니다.'
        else:
          answer = '동영상 촬영을 종료했습니다.'
        matched = False if answer == None else True
      if item[0] == '이번':
        answer = self.bot_db["일정"](string)
        matched = False if answer == None else True
      if item[0] == '미세먼지':
        answer = self.bot_db[item[0]](string)
        matched = False if answer == None else True
      elif item[1] == 'NNG':
        for key in self.bot_db.items():
          if key[0] == item[0]:
            answer = self.bot_db[key[0]](string, voice)
            matched = False if answer == None else True
        for key in motion_db:
          if key == item[0]:
            answer = self.pd.motion(motion_db[key])
            matched = False if answer == None else True

    print('match : {}, string : {}'.format(matched, string))
    if matched == False:
      answer = self.pd.chat(string)

    self.voice_answer.append(answer)
    self.pd.speak('<speak>'+answer+'</speak>')
    return answer