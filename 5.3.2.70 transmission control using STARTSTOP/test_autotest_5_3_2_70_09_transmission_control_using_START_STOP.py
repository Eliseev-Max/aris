"""
Проверка сохранения последовательности N(S) - N(R) после STOPDT -> STARTDT
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

def test_autotest_5_3_2_70_09_trans_con_us_START_STOP(IP,PORT,t1_SERVER):
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
    cvalue = telnet_checker()
    client.connect()

    
    client.sendStartDT()
    
    i = 0

    testfr = u_frame_checker(client)

### Проверка STARTDT_ACT
    while (str(testfr[-1].data.type) != "STARTDT_CON") and (i <= t1_SERVER + 1):
        testfr = u_frame_checker(client)
        time.sleep(0.2)
 
        i += 0.2

    if i >= t1_SERVER + 1:
        testcon = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.70.09: !Ошибка:     После отправки команды STARTDT_ACT клиентом не получен STARTDT_CON"
        log(FILENAME,testcon)
        assert str(testfr[-1].data.type) == "STARTDT_CON", "Не получен STARTDT_CON"
  

    for i in range(2):
        client.sendIO(spObj, rkts.CauseOfTransmission.COT_ACTIVATION, 1)

    spGenerator(IP,cvalue,2)

    time.sleep(1)

    I_frame_last_Ns = int(client.events()[-1].data.recvCount)
    I_frame_last_Nr = int(client.events()[-1].data.sentCount)

    client.sendStopDT()
    i = 0
### Проверка STOPDT_ACT
    testfr = u_frame_checker(client)


    while (str(testfr[-1].data.type) != "STOPDT_CON") and (i <= t1_SERVER + 1):
        testfr = u_frame_checker(client)
        time.sleep(0.2)
 
        i += 0.2

    if i >= t1_SERVER + 1:
        testcon = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.70.09: !Ошибка:     После отправки команды STOPDT_ACT клиентом не получен STOPDT_CON"
        log(FILENAME,testcon)
        assert str(testfr[-1].data.type) == "STOPDT_CON", "Не получен STOPDT_CON"

    time.sleep(1)
    recv_I_frame_last = []
    count_events = int(client.eventsCount)
   
    for Idad in range(0,count_events,1):
        if client.events()[Idad].type in type_I_frame:
            recv_I_frame_last.append(client.events()[Idad])
    
    I_frame_last_Ns = int(recv_I_frame_last[-1].data.recvCount)
    I_frame_last_Nr = int(recv_I_frame_last[-1].data.sentCount)
    

    cvalues = telnet_checker()

    client.sendStartDT()
    
    i = 0

    testfr = u_frame_checker(client)

### Проверка STARTDT_ACT
    while (str(testfr[-1].data.type) != "STARTDT_CON") and (i <= t1_SERVER + 1):
        testfr = u_frame_checker(client)
        time.sleep(0.2)
 
        i += 0.2

    if i >= t1_SERVER + 1:
        testcon = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.70.09: !Ошибка:     После отправки команды STARTDT_ACT клиентом не получен STARTDT_CON"
        log(FILENAME,testcon)
        assert str(testfr[-1].data.type) == "STARTDT_CON", "Не получен STARTDT_CON"
    

    spGenerator(IP,cvalues,2)
    time.sleep(0.5)

    count_events2 = int(client.eventsCount)

    result_events = count_events - count_events2

    recv_I_frame_first = []


   
   
    for Idad in range(result_events,0,1):
        if client.events()[Idad].type in type_I_frame:
            recv_I_frame_first.append(client.events()[Idad])
    

    I_frame_first_Ns = int(recv_I_frame_first[0].data.recvCount)
    I_frame_first_Nr = int(recv_I_frame_first[0].data.sentCount)

    resultNS = I_frame_first_Ns - I_frame_last_Ns
    resultNR = I_frame_first_Nr - I_frame_last_Nr
    print(I_frame_last_Ns)
    print(I_frame_first_Ns)

    if resultNS == 1 and resultNR == 0:
        res = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.70.09: Пройдено:     Неизменность порядковых номеров после STOPDT/STARTDT"
        log(FILENAME,res)
    else:
        if resultNS != 1:
            reserrs = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.70.09: !Ошибка:     Порядковый номер передачи N(S) не сохранен после STOPDT/STARTDT"
            log (FILENAME,reserrs)
            assert resultNS == 1, "Порядковый номер передачи N(S) не сохранен после STARTDT/STOPDT"
        
        if resultNR != 0:
            reserrR = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.70.09: !Ошибка:     Порядковый номер передачи N(R) не сохранен после STOPDT/STARTDT"
            log (FILENAME,reserrR)
            assert resultNS == 0, "Порядковый номер передачи N(R) не сохранен после STOPDT/STARTDT"
        
        assert resultNS == 1 and resultNR == 0, "Сохранение порядковых номеров после STOPDT/STARTDT"
        
