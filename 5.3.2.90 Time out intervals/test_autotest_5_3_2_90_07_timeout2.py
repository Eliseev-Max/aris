
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
#### Проверка отсутсвия сброса таймера t2 U и S кадрами
def test_timeout2_autotest_5_3_2_90_7(t2_SERVER,det,IP,PORT):


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

    client.sendStartDT()
    time.sleep(0.5)

    client.sendIO(spObj, rkts.CauseOfTransmission.COT_ACTIVATION, 1)
    time.sleep(0.5*t2_SERVER)

    client.sendTestAct()
    time.sleep(0.5)
    client.sendSFrame()
    time.sleep(t2_SERVER + det)

    count_events = int(client.eventsCount)

    recv_S_frame = []
    for num in range(0,count_events,1):
        if client.events()[num].type == rkts.EventType.S_FRAME:
            recv_S_frame.append(client.events()[num])

    valSframeU = int(recv_S_frame[-1].data.sVal)

    if len(recv_S_frame) == 0:
        errSU = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.7: !Ошибка:     Таймер t2 сброшен U кадром или S кадром"
        log(FILENAME,errSU)
        assert len(recv_S_frame) != 0, "Проверка таймера t2, сброс таймера t2 U и S кадрами"
    else:
        valSframeU = int(recv_S_frame[-1].data.sVal)
    
    if valSframeU == 1:
        prt2passed = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.7: Пройдено:     Отсутствие сброса таймера t2 U и S кадрами"
        log(FILENAME,prt2passed)
    else:
        errt2U = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.7: !Ошибка:     Последний отправленный I кадр серверу не был подтвержден после таймера t2"
        log(FILENAME,errt2U)
        assert valSframeU == 1, "Проверка таймера t2, сброс таймера t2 U и S кадрами"