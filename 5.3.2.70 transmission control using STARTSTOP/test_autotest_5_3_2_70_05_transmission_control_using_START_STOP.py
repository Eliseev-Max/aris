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

def test_autotest_5_3_2_70_05_trans_con_us_START_STOP(IP,PORT,W_SERVER):
    
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
    cvalue = telnet_checker()
    client.sendStartDT()

    spGenerator(IP,cvalue,2,0)
    time.sleep(1)
    client.sendSFrame()

    time.sleep(2)

    for i in range(0,W_SERVER,1):
        client.sendIO(spObj, rkts.CauseOfTransmission.COT_ACTIVATION, 1)

    time.sleep(2)

    client.sendTestAct()
    time.sleep(2)

    for ev in client.events():
        if ev.type == rkts.EventType.CONNECTION_CLOSED:
            closecon = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.70.05: !Ошибка:     Сервер разорвал TCP соединение после обмена кадрами"
            assert ev.type == rkts.EventType.CONNECTION_CLOSED,"Сервер разорвал TCP соединение после обмена кадрами"
            log(FILENAME,closecon)

        else: continue 
    

    recv_I_frame = []
    recv_S_frame = []
    count_events = int(client.eventsCount)
   
    for Idad in range(0,count_events,1):
        if client.events()[Idad].type in type_I_frame:
            recv_I_frame.append(client.events()[Idad])
        if client.events()[Idad].type == rkts.EventType.S_FRAME:
            recv_S_frame.append(client.events()[Idad])
    
    if len(recv_I_frame) == 0:
        Irec = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.70.05: !Ошибка:     Не получены I кадры от сервера после STARTDT"
        log(FILENAME,Irec)
        assert len(recv_I_frame) != 0, "Не получены I кадры после STARTDT"
    
    if len(recv_S_frame) == 0:
        Irec = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.70.05: !Ошибка:     Не получен S кадр от сервера после STARTDT"
        log(FILENAME,Irec)
        assert len(recv_I_frame) != 0, "Не получены I кадры после STARTDT"
    
    testfr = u_frame_checker(client)

    if str(testfr[-1].data.type) == "TESTFR_CON":
        post3 = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.70.05: Пройдено:     Обмен кадрами при активном соединении"
        log(FILENAME,post3)
    else:
        conframe = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.70.05: !Ошибка:     После отправки команды TESTFR_ACT клиентом не получен TESTFR_CON"
        log(FILENAME,conframe)
        assert str(testfr[-1].data.type) == "TESTFR_CON", "Проверка таймера t3, сброс таймера U кадром"