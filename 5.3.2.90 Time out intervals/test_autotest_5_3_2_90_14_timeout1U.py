
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

def test_timeout1U_autotest_5_3_2_90_14(t1_SERVER,t3_SERVER,det,IP,PORT):
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

    time.sleep(t3_SERVER + det)

    client.sendTestCon()
    time.sleep(t1_SERVER + det)

    proverTime = 0
    for ev in client.events():
        if ev.type == rkts.EventType.CONNECTION_CLOSED:
            proverTime = int(ev.timestamp/1000)
            client.disconnect()
        else: continue
    
    if proverTime == 0:
        correctt1 = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.14: Пройдено:     Таймер t1 был сброшен команой TESTFR_CON"
        log(FILENAME,correctt1)
    else:
        notcorrectt1 = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.14: !Ошибка:     Таймер t1 не был сброшен командой TESTFR_CON"
        log(FILENAME,notcorrectt1)
        assert proverTime == 0, "Проверка таймера t1 (U Frame)"