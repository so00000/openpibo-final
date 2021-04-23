# openpibo-final
## 실행

```bash
~ $ git clone "https://github.com/themakerrobot/openpibo.git"
~ $ git clone "https://github.com/themakerrobot/openpibo-data.git"
~ $ cd openpibo
~/openpibo $ sudo ./install.sh
...
REBOOT NOW? [y/N] # y입력 또는 N 입력 후 sudo reboot

~/openpibo $ sudo ./control_mic_volume.sh

~ $ git clone https://github.com/so00000/openpibo-final.git
~ $ cd openpibo-final
~/openpibo-final $ python3 main.py
```

http://localhost:8888/test 경로에서 진행하면 됩니다.



## 파이보에게 명령 내리기

1. http://localhost:8888/test 에서 text 입력
2. http://localhost:8888/test에서 `음성` 버튼 클릭
3. 머리 터치