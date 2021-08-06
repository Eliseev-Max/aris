"""
Проверка поведения сервера, имеющего неподтверждённые I-кадры, после получения им STOPDT ACT
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

def test_autotest_5_3_2_70_10_trans_con_us_START_STOP(IP,PORT,t1_SERVER):

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

    client.sendStartDT()
    
    i = 0

    testfr = u_frame_checker(client)

# Проверка STARTDT_ACT
    while (str(testfr[-1].data.type) != "STARTDT_CON") and (i <= t1_SERVER + 1):
        testfr = u_frame_checker(client)
        time.sleep(0.2)
 
        i += 0.2

    if i >= t1_SERVER + 1:
        testcon = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.70.10: !Ошибка:     После отправки команды STARTDT_ACT клиентом не получен STARTDT_CON"
        log(FILENAME,testcon)
        assert str(testfr[-1].data.type) == "STARTDT_CON", "Не получен STARTDT_CON"


    client.sendIO(spObj, rkts.CauseOfTransmission.COT_ACTIVATION, 1)
    client.sendIO(spObj, rkts.CauseOfTransmission.COT_ACTIVATION, 1)

    prover = 2
    for el in client.events():
        if el.type == rkts.EventType.S_FRAME:
            client.sendIO(spObj, rkts.CauseOfTransmission.COT_ACTIVATION, 1)
            client.sendIO(spObj, rkts.CauseOfTransmission.COT_ACTIVATION, 1)
            prover = prover + 2
    # В созданном классе IEC104_Client в методе отправки I-кадров клиентом 
    # добавить счётчик отправленных I-кадров (метод класса)
    time.sleep(0.5)


    client.sendStopDT()
    i = 0
### Проверка STOPDT_ACT
    testfr = u_frame_checker(client)


    while (str(testfr[-1].data.type) != "STOPDT_CON") and (i <= t1_SERVER + 1):
        testfr = u_frame_checker(client)
        time.sleep(0.2)
 
        i += 0.2

    if i >= t1_SERVER + 1:
        testcon = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.70.10: !Ошибка:     После отправки команды STOPDT_ACT клиентом не получен STOPDT_CON"
        log(FILENAME,testcon)
        assert str(testfr[-1].data.type) == "STOPDT_CON", "Не получен STOPDT_CON"



    count_events = int(client.eventsCount)

    recv_S_frame = []
   
    for Idad in range(0,count_events,1):
        if client.events()[Idad].type == rkts.EventType.S_FRAME:
                recv_S_frame.append(client.events()[Idad].data.sVal)
               
            

    ##Если S кадр не будет отправляться автоматически перед STOPDT то изменить элемент на [0]
    if recv_S_frame[1] != prover:
        err11 = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.70.10: !Ошибка:     Сервер не подтвердил все I кадры клиента после STOPDT_ACT"
        log(FILENAME,err11)
        assert recv_S_frame[1] == prover
    
    testfr = u_frame_checker(client)

    if str(testfr[-1].data.type) == "STOPDT_CON":
        post3 = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.70.10: Пройдено:     Подтверждение сервером I кадров после STOPDT_ACT"
        log(FILENAME,post3)
    else:
        conframe = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.70.10: !Ошибка:     После отправки команды STOPDT_ACT клиентом не получен STOPDT_CON"
        log(FILENAME,conframe)
        assert str(testfr[-1].data.type) == "STOPDT_CON", "Не получен STARTDT_CON"

            
