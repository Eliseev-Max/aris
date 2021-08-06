
import rkts
import os
import time
import datetime
from arisconnector import ArisConnector, ArisTelnetConnector as tnc
from Tools.tools import *

# Включение/отключение логирования
LOGGING = True
# Параметры сервера
PORT = 2404
IP = "10.1.31.10"
W_SERVER = 8
K_SERVER = int(3/2 *W_SERVER)
t1_SERVER = 15
t2_SERVER = 10
t3_SERVER = 20
det = 2
KServer = str(K_SERVER)
WServer = str(W_SERVER)
t1server = str (t1_SERVER)
t2server = str (t2_SERVER)
t3server = str (t3_SERVER)

os.chdir(os.path.dirname(os.path.abspath(__file__)))
FILENAME = "Timeout_log.txt"


type_I_frame = (rkts.EventType.I_FRAME_PROCESS_INFO_MON_DIR,
                rkts.EventType.END_OF_INIT,
                rkts.EventType.I_FRAME_PROCESS_INFO_CONTR_DIR)

def test_timeout1U_autotest_5_3_2_90_12(t3_SERVER,t1_SERVER,det,IP,PORT):
    client = rkts.Client60870(port=PORT,
                                address=IP,
                                bufferSize=1000)
    client.autoAckReachedW = True          #Sending S-frame after reaching W parameter
    client.timerT2Work = False              #Sending S-frame after t2 timeout
    client.timerT1Work = False
    client.autoAckTestFrame = False
    client.timerT3Work = False               #Sending U-frame TESTFR_Ack after the configured time period t3
    t1server = str (t1_SERVER)
    spObj = rkts.IOSinglePoint()
#### Проверка корректной работы таймера t1, отсутствие сброса таймера t1 на I,S,U кадры


    client.connect()
    time.sleep(t3_SERVER + det + t1_SERVER + det)

    if len( u_frame_checker(client)) != 1:
        assert len(u_frame_checker(client)) == 1, "Проверка таймера t1 (U Frame), Не получен TESTFR_ACT"
    conCloseTime = 0
    Uframet1 = u_frame_checker(client)[-1].timestamp/1000

    for ev in client.events():
        if ev.type == rkts.EventType.CONNECTION_CLOSED:
            conCloseTime = int(ev.timestamp/1000)
            result3U = int( conCloseTime - Uframet1)
            client.disconnect()
        else: continue

    if conCloseTime == 0:
            Ut1err = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.12: !Ошибка:     После получения TESTFR_ACT через время t1 сервер не разорвал соединение"
            log(FILENAME,Ut1err)
            assert conCloseTime != 0, "Проверка таймера t1 (U frame), корректная работа"
    
    if t1_SERVER - 1 <= result3U <= t1_SERVER + 1:
        dopt1 = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.12: Пройдено:     Корректная работа таймера t1 (U frame)"
        log(FILENAME,dopt1)
    else:
        sresult1U = str(result3U)
        errdopt1 = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.12: !Ошибка:     (t1 U Frame) Полученное значение t1 ["+sresult1U+"] не соответствует заданному["+ t1server +" c])\n"
        log(FILENAME,errdopt1)
        assert t1_SERVER - 1 <= result3U <= t1_SERVER + 1, "Проверка таймера t1 (U frame)"