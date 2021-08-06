"""
Ответ сервера на STARTDT_ACT и STOPDT_ACT
"""
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


type_I_frame = (rkts.EventType.I_FRAME_PROCESS_INFO_MON_DIR,
                rkts.EventType.END_OF_INIT,
                rkts.EventType.I_FRAME_PROCESS_INFO_CONTR_DIR)

def test_autotest_5_3_2_70_04_trans_con_us_START_STOP(IP,PORT,W_SERVER):

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    FILENAME = "transmissionSTARTSTOP_log.txt"
    
    client = rkts.Client60870(port=PORT,
                              address=IP,
                              bufferSize=1000)
    client.autoAckReachedW = True         #Sending S-frame after reaching W parameter
    client.timerT2Work = False              #Sending S-frame after t2 timeout
    client.timerT1Work = False
    client.autoAckTestFrame = False
    client.timerT3Work = False               #Sending U-frame TESTFR_Ack after the configured time period t3
    
    spObj = rkts.IOSinglePoint()

    
    client.connect()
    time.sleep(0.5)
    client.sendStartDT()

    i = 0

    testfr = u_frame_checker(client)

    while (str(testfr[-1].data.type) != "STARTDT_CON") and (i <= t1_SERVER + 1):
        testfr = u_frame_checker(client)
        time.sleep(0.2)
 
        i += 0.2

    if i >= t1_SERVER + 1:
        testcon = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.70.04: !Ошибка:\t\
            После отправки команды STARTDT_ACT клиентом не получен STARTDT_CON"
        log(FILENAME,testcon)
        assert str(testfr[-1].data.type) == "STARTDT_CON", "Не получен STARTDT_CON"

    time.sleep(0.5)

    client.sendStopDT()

    i = 0

    testfr = u_frame_checker(client)


    while (str(testfr[-1].data.type) != "STOPDT_CON") and (i <= t1_SERVER + 1):
        testfr = u_frame_checker(client)
        time.sleep(0.2)
 
        i += 0.2

    if i >= t1_SERVER + 1:
        testcon = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.70.04: !Ошибка:     После отправки команды STOPDT_ACT клиентом не получен STOPDT_CON"
        log(FILENAME,testcon)
        assert str(testfr[-1].data.type) == "STOPDT_CON", "Не получен STOPDT_CON"


    post3 = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.70.04: Пройдено:     Ответ на STARTDT_ACT и STOPDT_ACT"
    log(FILENAME,post3)


