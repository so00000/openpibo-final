import datetime
import pickle
from bs4 import BeautifulSoup as bs
from datetime import datetime, timedelta
from pprint import pprint
import requests
import re

news_keys = {
  '종합':'http://fs.jtbc.joins.com/RSS/newsrank.xml', 
  '정치':'http://fs.jtbc.joins.com/RSS/politics.xml', 
  '경제':'http://fs.jtbc.joins.com/RSS/economy.xml', 
  '사회':'http://fs.jtbc.joins.com/RSS/society.xml', 
  '스포츠':'http://fs.jtbc.joins.com/RSS/sports.xml', 
  '연예':'http://fs.jtbc.joins.com/RSS/entertainment.xml',
}

CALENDAR_PATH = '/home/pi/openpibo-final/data/calendar_db'

def weather_bot(string=None, voice=False):
  return_text = ''
  html = requests.get('https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=1&ie=utf8&query=%EB%82%A0%EC%94%A8')

  soup = bs(html.text, 'html.parser')
  main_data = soup.find('div', {'class':'weather_box'})
  sub_data = soup.find('div', {'class': 'detail_box'})
  dust = []
 
  if '오늘' in string:
    if '미세먼지' in string:
      for i in sub_data.select('dd'):
        dust.append(i.text)
      today_finedust = dust[0][:-2] + " " + dust[0][-2:]
      today_ultrafine = dust[1][:-2] + " " + dust[1][-2:]
      today_ozone = dust[2][:-2] + " " + dust[2][-2:]
      return_text = '오늘 미세먼지는 {}이고, 초미세먼지는 {}입니다.'.format(today_finedust, today_ultrafine)
    else:
      today_main_data = main_data.find('div', {'class':'main_info'})
      today_temp = today_main_data.find('span', {'class':'todaytemp'}).text
      today_feel_temp = today_main_data.find('p', {'class':'cast_txt'}).text
      return_text = '오늘 기온은 {}°, {}.'.format(today_temp, today_feel_temp)

  elif '내일' in string:
    if '미세먼지' in string:
      tomorrow = soup.find('div', {'class': 'tomorrow_area'})
      tomorrow_dust = tomorrow.find_all('span', {'class': 'indicator'})
      dust_data = [d.get_text().strip() for d in tomorrow_dust]

      morning_finedust = dust_data[0][-2:]
      afternoon_finedust = dust_data[1][-2:]
      return_text = '내일 미세먼지는 오전 {}, 오후 {}입니다.'.format(morning_finedust, afternoon_finedust)
    else:
      item = soup.select('.date_info')
      temp  = item[1].select('dd')
      for i in temp:
        k = i.text.strip()
      tomorrow_temp = k.split('/')
      morning_temp = tomorrow_temp[0]
      afternoon_temp = tomorrow_temp[1]
      return_text = '내일 최저기온은 {}, 최고기온은 {}예요.'.format(morning_temp, afternoon_temp)

  else:
    if '미세먼지' in string:
      return_text = '오늘 또는 내일 미세먼지만 알 수 있어요.'
    else:
      return_text = '오늘 또는 내일 날씨만 알 수 있어요.'

  return return_text

news_idx = 1
category = []
move = True
def news_bot(string=None, voice=False):
  global news_idx, category, move
  return_text = '뉴스가 없어요. '

  for key,value in news_keys.items():
    if key in string:
      if len(category) == 0:
        category.append(key)
      else:
        pre_category = category.pop()
        if pre_category != key:
          news_idx = 1
        category.append(key)
      news_cat = value 
      rss = requests.get(news_cat)
      rss.encoding = 'utf-8' # 한글깨짐현상 해결
      text = rss.text

      soup = bs(text, 'html.parser')
      items = soup.select('title')

      if "다음" in string:
        news_idx += 3
        if news_idx > len(items):
          news_idx -= 3
          move = False
          return_text = '마지막 뉴스입니다. 다음 뉴스가 없어요.'
      elif "이전" in string:
        news_idx -= 3
        if news_idx < 1:
          news_idx += 3
          move = False
          return_text = '첫 번째 뉴스입니다. 이전 뉴스가 없어요.'

      if move:
        # return_text = '뉴스를 알려줄게요. '
        return_text = ' '
        for item in items[news_idx:news_idx+3]:
          # print('result : {}'.format(item))
          omg = str(item)
          omg = omg.replace('&amp;', '&')
          omg = re.sub('<.+?>', '', omg, 0).strip()
          return_text = return_text + omg + '. '
      move = True
  return return_text

def check_date(date_string):
  try:
    datetime.strptime(date_string, '%Y/%m/%d')
    return True
  except ValueError:
    return False

def calendar_bot(string=None, voice=False):
  with open(CALENDAR_PATH, "rb") as f:
    db = pickle.load(f)
  return_text = ''
 # 등록 삭제 조회

  #db = {"2020/11/26":["청소","식사","시험"]}
  # 입력방법 
  # - 일정등록:2020/11/27:집안청소
  # - 일정삭제:2020/11/27:1
  # - 일정조회:2020/11/27
  # - 일정초기화
  # - 오늘 일정 조회
  # - 내일 일정 조회
  if voice == True:
    if "초기화" not in string:
      if ("오늘" not in string and "내일" not in string and "이번" not in string) or ("조회" not in string and "알려줘" not in string):
        return "음성으로는 오늘과 내일 일정 조회와 초기화만 할 수 있어요." 

  if "초기화" in string:
    db = {}
    with open(CALENDAR_PATH, "w+b") as f:
      pickle.dump(db, f)
    return_text = '일정을 초기화했어요.'
    
  elif "등록" in string:
    items = string.split(':')
    if items[1] not in db:
      db[items[1]] = []

    db[items[1]].append(items[2])

    with open(CALENDAR_PATH, "w+b") as f:
      pickle.dump(db, f)
    return_text = '일정 등록했어요.'

  elif "삭제" in string:
    items = string.split(':')
    return_text = '{}, 삭제할 일정이 없어요.'.format(items[1])

    if items[1] in db:
      if len(db[items[1]]) > int(items[2])-1:
        delcal = db[items[1]].pop(int(items[2])-1)
      with open(CALENDAR_PATH, "w+b") as f:
        pickle.dump(db, f)
      return_text = '일정 삭제했어요.'

  elif "조회" in string or "알려줘" in string:
    if "오늘" in string:
      now = datetime.now()
      date = "{}/{}/{}".format(now.year, now.month, now.day)
    elif "내일" in string:
      tom = datetime.now() + timedelta(days=1)
      date = "{}/{}/{}".format(tom.year, tom.month, tom.day)
    elif "이번" in string:
      now = datetime.now()
      monday = now - timedelta(days = now.weekday())  # 이번 주 월요일
      sunday = monday + timedelta(days = 6) # 이번 주 일요일
      remain_days = (sunday - now).days # 이번 주 남은 일 수
      dates = []
      schedule_list = ""
      total_schedule = 0
      for i in range(remain_days+1):
        day = now + timedelta(days=i)
        dates.append((day.year, day.month, day.day))

      for j in range(len(dates)):
        date = "{}/{}/{}".format(dates[j][0], dates[j][1], dates[j][2]) 
        if date in db:
          items = db[date]
          schedule_list += "{} {}건, ".format(date, len(items))
          total_schedule += len(items)
      if len(schedule_list) == 0:
        return_text = "이번 주 일정이 없어요."
      else:
        return_text = schedule_list[:-2] + " 총 {}건의 일정이 있어요.".format(total_schedule)
      return return_text
    else:
      tmp = string.split(':')
      date = tmp[1] if check_date(tmp[1]) else ""
     
    if date in db:
      items = db[date]
      for item in items:
        return_text = return_text + item + ". "
    else: 
      return_text = "{}, 일정이 없어요.".format(date)
  else:
    return_text = '등록, 삭제, 조회만 할 수 있어요.'

  return return_text
