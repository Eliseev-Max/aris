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

def test_autotest_5_3_2_70_01_trans_con_us_START_STOP(IP, PORT, t1_SERVER):
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
    
    
    cvalue = telnet_checker()
    client.connect()

    spGenerator(IP,cvalue,2)
    time.sleep(0.5)
    recv_I_frame = []
    count_events = int(client.eventsCount)
   
    for Idad in range(0,count_events,1):
        if client.events()[Idad].type in type_I_frame:
            recv_I_frame.append(client.events()[Idad])
    
    if len(recv_I_frame) != 0:      # Подумать о реализации через количество событий...
        Irec = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.70.01: !Ошибка:     Получены I кадры до STARTDT"
        log(FILENAME,Irec)
       # assert len(recv_I_frame) == 0, "Получены I кадры до STARTDT"
        raise AssertionError("Получены I кадры до STARTDT")

    client.sendTestAct()
    i = 0

    testfr = u_frame_checker(client)

    TIMEOUT = 15
    current_time = time.time()

    #while str(testfr[-1].data.type) != "TESTFR_CON":
    # str(u_frame_checker(client)[-1].data.type) != "TESTFR_CON":
    while True:
        if time.time() > (current_time + TIMEOUT):
            message = "Time is up"
            raise AssertionError(message)

        if str(u_frame_checker(client)[-1].data.type) == "TESTFR_CON":
            # u_frame_checker(client)[-1].timestamp
            break

    # if i >= t1_SERVER + 1:
    #     testcon = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.70.01: !Ошибка:     Не получен TESTFR_CON"
    #     log(FILENAME,testcon)
    #     assert str(testfr[-1].data.type) == "TESTFR_CON", "Не получен TESTFR_CON"

    for ev in client.events():
        if ev.type == rkts.EventType.CONNECTION_CLOSED:
            closecon = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.70.01: !Ошибка:     Сервер разорвал TCP соединение после отправки TESTFR"
            log(FILENAME,closecon)
            assert ev.type == rkts.EventType.CONNECTION_CLOSED, "Сервер разорвал TCP соединение после отправки TESTFR"
        else: continue 
    contest = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.70.01: Пройдено:     Получен TESTFR_CON, обмен U кадров в Stopped connection(после нового TCP соединения), I кадры не получены"
    log(FILENAME,contest)
    


    
    
    


