
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

def test_timeout2_autotest_5_3_2_90_6(t2_SERVER,det,IP,PORT):

    client = rkts.Client60870(port=PORT,
                              address=IP,
                              bufferSize=1000)
    client.autoAckReachedW = True          #Sending S-frame after reaching W parameter
    client.timerT2Work = False              #Sending S-frame after t2 timeout
    client.timerT1Work = False
    client.autoAckTestFrame = False
    client.timerT3Work = False               #Sending U-frame TESTFR_Ack after the configured time period t3
    
    spObj = rkts.IOSinglePoint()

#### Проверяем сброс таймера t2 I кадром    
    client.connect()

    cvalue = telnet_checker()
    client.sendStartDT()
    time.sleep(0.5)

    client.sendIO(spObj, rkts.CauseOfTransmission.COT_ACTIVATION, 1)
    time.sleep(0.5*t2_SERVER)
    
    spGenerator(IP,cvalue, 1)
    
    time.sleep(0.2*t2_SERVER + det)
    count_events = int(client.eventsCount)
    i = 0
    for s in range (0,count_events,1):
        if client.events()[s].type == rkts.EventType.S_FRAME:
            i = i + 1

    if i != 0:
        errIt2 ="\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.6: !Ошибка:     Полученный I кадр от сервера не сбросил таймер t2"
        log(FILENAME,errIt2)
        assert i != 0, "Проверка таймера t2, сброс таймера I кадром"
    else:
        prodt2 = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.6: Пройдено:     Таймер t2 сбросился I кадром"
        log(FILENAME,prodt2)

