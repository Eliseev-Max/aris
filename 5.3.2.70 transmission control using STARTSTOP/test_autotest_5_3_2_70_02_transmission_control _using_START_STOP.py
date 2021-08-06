"""
Проверка закрытия TCP-соединения после получения I-кадра в Stopped Connection (после нового TCP-соединения)
Порядок действий:
1. Устанавливаем TCP-соединение
2. Отправить серверу I-кадр

Ожидаемый результат:
Сервер разрывает TCP-соединение

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
det = 2         # Погрешность
CICLE_TIME = 2

# Это не нужно вообще
# # KServer = str(K_SERVER)
# WServer = str(W_SERVER)
# t1server = str (t1_SERVER)
# t2server = str (t2_SERVER)
# t3server = str (t3_SERVER)


def test_autotest_5_3_2_70_02_trans_con_us_START_STOP(IP,PORT):

    FILENAME = "transmissionSTARTSTOP_log.txt"

# !!! Создать класс IEC104_Client()    

    client = rkts.Client60870(port=PORT,
                              address=IP,
                              bufferSize=1000)
    client.autoAckReachedW = True         #Sending S-frame after reaching W parameter
    client.timerT2Work = False              #Sending S-frame after t2 timeout
    client.timerT1Work = False
    client.autoAckTestFrame = False
    client.timerT3Work = False               #Sending U-frame TESTFR_Ack after the configured time period t3
    
    spObj = rkts.IOSinglePoint()        # I-frame type
    
    client.connect()
    time.sleep(0.2)

    client.sendIO(spObj, rkts.CauseOfTransmission.COT_ACTIVATION, 1)
    
 
    start_time = time.time()
    while True:
        if client.events()[-1].type == rkts.EventType.CONNECTION_CLOSED:
            print(f'{time.strftime("%Y%m%d_%H.%M")} - Сервер разорвал TCP соединение после отправки I кадра до STARTDT')
            closecon = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.70.02: Пройдено:     Сервер разорвал TCP соединение после отправки I кадра до STARTDT"
            log(FILENAME,closecon)
            break

        if time.time()>(start_time + CICLE_TIME):
            closecon = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.70.02: !Ошибка:     Сервер не разорвал TCP соединение после отправки I кадра до STARTDT"
            log(FILENAME,closecon)
            raise AssertionError("Сервер не разорвал TCP соединение после отправки I кадра до STARTDT")



    


    