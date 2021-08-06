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


os.chdir(os.path.dirname(os.path.abspath(__file__)))
FILENAME = "Timeout_log.txt"

KServer = str(K_SERVER)
WServer = str(W_SERVER)
t1server = str (t1_SERVER)
t2server = str (t2_SERVER)
t3server = str (t3_SERVER)


type_I_frame = (rkts.EventType.I_FRAME_PROCESS_INFO_MON_DIR,
                rkts.EventType.END_OF_INIT,
                rkts.EventType.I_FRAME_PROCESS_INFO_CONTR_DIR)


def test_timeout1I_autotest_5_3_2_90_1(t1_SERVER,det,IP,PORT):
    
    t1server = str (t1_SERVER)
   
    client = rkts.Client60870(port=PORT,
                              address=IP,
                              bufferSize=1000)
    client.autoAckReachedW = True         #Sending S-frame after reaching W parameter
    client.timerT2Work = False              #Sending S-frame after t2 timeout
    client.timerT1Work = False
    client.autoAckTestFrame = False
    client.timerT3Work = False               #Sending U-frame TESTFR_Ack after the configured time period t3
    
    spObj = rkts.IOSinglePoint()

    
    cvalue = telnet_checker()
    client.connect()
    client.sendStartDT()


    spGenerator(IP,cvalue, 2, 0.4*t1_SERVER)

    time.sleep(t1_SERVER + det)
    recv_I_frame = []
    count_events = int(client.eventsCount)
   
    for Idad in range(0,count_events,1):
        if client.events()[Idad].type in type_I_frame:
            recv_I_frame.append(client.events()[Idad])

    twIframetime = int(recv_I_frame[0].timestamp/1000)
    thIframetime = int(recv_I_frame[-1].timestamp/1000)

    conCloseTime = 0    
    for ev in client.events():
        if ev.type == rkts.EventType.CONNECTION_CLOSED:
            conCloseTime = int(ev.timestamp/1000)
            result12 = conCloseTime - twIframetime
            result13 = conCloseTime - thIframetime
            client.disconnect()
        else: continue 

    if conCloseTime == 0:
        t1err = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.1: !Ошибка:     После ожидания таймера t1 не был зафиксирован разрыв соединения (S кадр)"
        log (FILENAME,t1err)
        assert conCloseTime != 0, "Проверка таймера t1: не обнаружен разрыв соединения"

    if t1_SERVER - 1 <= result12 <= t1_SERVER + 1:
        t1pos = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.1: Пройдено:     Корректное срабатывание таймера t1"
        log(FILENAME, t1pos)
    else:
        if t1_SERVER - 1 <= result13 <= t1_SERVER + 1:
            t1neg1 = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.1: !Ошибка:    Таймер t1 сработал после последнего полученного I кадра\n"
            log(FILENAME,t1neg1)
            assert t1_SERVER - 1 <= result13 <= t1_SERVER + 1, "Проверка таймера t1: корректная работа"
        
        sresult12 = str(result12)
        t1neg = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.1: !Ошибка:    \nПолученное значение таймера t1 ["+sresult12 + " c] не соответствует заданному ["+ t1server +" c])\n"
        log(FILENAME, t1neg)
        assert t1_SERVER - 1 <= result12 <= t1_SERVER + 1, "Проверка таймера t1 (I кадр)"




