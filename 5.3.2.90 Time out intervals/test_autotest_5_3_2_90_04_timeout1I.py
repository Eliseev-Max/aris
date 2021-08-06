
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

def test_timeout1I_autotest_5_3_2_90_4(t1_SERVER,det,IP,PORT):
    bufferclear(IP,PORT)
    t1server = str (t1_SERVER)
    client = rkts.Client60870(port=PORT,
                              address=IP,
                              bufferSize=1000)
    client.autoAckReachedW = True          #Sending S-frame after reaching W parameter
    client.timerT2Work = False              #Sending S-frame after t2 timeout
    client.timerT1Work = False
    client.autoAckTestFrame = False
    client.timerT3Work = False               #Sending U-frame TESTFR_Ack after the configured time period t3
    
    spObj = rkts.IOSinglePoint()
    
    client.connect()
    cvalue = telnet_checker()

    client.sendStartDT()


    spGenerator(IP,cvalue, 2, 0.4*t1_SERVER)

    client.sendTestAct()

    time.sleep(0.6*t1_SERVER + det)

    
    recv_I_frame = []

    count_events = int(client.eventsCount) 

    for Idad in range(0,count_events,1):
        if client.events()[Idad].type in type_I_frame:
            recv_I_frame.append(client.events()[Idad])

    if len(recv_I_frame) < 2:
        assert len(recv_I_frame) >= 2, "Проверка таймера t1 (I Frame), Получены не все сгенерированные I кадры"
    
    firstIframetimeU = int(recv_I_frame[0].timestamp/1000)
    twIframetimeU = int(recv_I_frame[-1].timestamp/1000)

    conCloseTimeU = 0

    for ev in client.events():
        if ev.type == rkts.EventType.CONNECTION_CLOSED:
            conCloseTimeU = int(ev.timestamp/1000)
            result11U = conCloseTimeU - firstIframetimeU
            result12U = conCloseTimeU - twIframetimeU
        else: continue 
            

    if conCloseTimeU == 0:
        t1err = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.4: !Ошибка:     После ожидания таймера t1 не был зафиксирован разрыв соединения (U кадр)"
        log (FILENAME,t1err)
        assert conCloseTimeU != 0, "Проверка таймера t1, нет разрыва TCP"

    if t1_SERVER - 1 <= result11U <= t1_SERVER + 1:
        t1pos = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.4: Пройдено:     Корректное срабатывание таймера t1, отсутсвие сброса таймера t1 U кадром"
        log(FILENAME, t1pos)
    else:
        if t1_SERVER - 1 <= result12U <= t1_SERVER + 1:
            t1neg1 = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.4: !Ошибка:    Таймер t1 был сброшен после отправки серверу U кадра\n"
            log(FILENAME,t1neg1)
            assert t1_SERVER - 1 <= result11U <= t1_SERVER + 1, "Проверка таймера t1: сброс таймера U кадр"
        
        sresult11 = str(result11U)
        t1neg = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.4: !Ошибка:     Полученное значение таймера t1 ["+sresult11 + " c] не соответствует заданному ["+ t1server +" c])\n"
        log(FILENAME, t1neg)
        assert t1_SERVER - 1 <= result11U <= t1_SERVER + 1, "Проверка таймера t1 (I кадр)"
