# Объединить два теста с помощью pytest parametrize
"""
Проверка закрытия TCP-соединения после получения S-кадра в Stopped Connection (после нового TCP-соединения)
Порядок действий:
1. Устанавливаем TCP-соединение
2. Отправить серверу S-кадр

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
CICLE_TIME = 2
det = 2




KServer = str(K_SERVER)
WServer = str(W_SERVER)
t1server = str (t1_SERVER)
t2server = str (t2_SERVER)
t3server = str (t3_SERVER)


type_I_frame = (rkts.EventType.I_FRAME_PROCESS_INFO_MON_DIR,
                rkts.EventType.END_OF_INIT,
                rkts.EventType.I_FRAME_PROCESS_INFO_CONTR_DIR)

def test_autotest_5_3_2_70_03_trans_con_us_START_STOP(IP,PORT):
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

    client.sendSFrame()

    start_time = time.time()
    while True:
        if client.events()[-1].type == rkts.EventType.CONNECTION_CLOSED:
            print(f'{time.strftime("%Y%m%d_%H.%M")} - Сервер разорвал TCP соединение после отправки I кадра до STARTDT')
            closecon = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.70.03: Пройдено:\t\
                Сервер разорвал TCP соединение после отправки S кадра в Stopped connection (после нового TCP  соединения)"
            log(FILENAME,closecon)
            break

        if time.time()>(start_time + CICLE_TIME):
            closecon = f'\n{time.strftime("%Y%m%d_%H.%M")} Autotest 5.3.2.70.03: !Ошибка:\t\
                Сервер не разорвал TCP соединение после отправки S кадра в Stopped \
                    connection (после нового TCP  соединения)'
            log(FILENAME,closecon)
            raise AssertionError("Сервер не разорвал TCP соединение после отправки S кадра до STARTDT")


    i = 0
    while (client.events()[-1].type != rkts.EventType.CONNECTION_CLOSED) and (i <= 2):

        time.sleep(0.2)
        i+= 0.2


    if i >= 2:
        closecon = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.70.03: !Ошибка:     Сервер не разорвал TCP соединение после отправки S кадра в Stopped connection (после нового TCP  соединения)"
        log(FILENAME,closecon)
        assert i <= 2, "Сервер не разорвал TCP соединение после отправки I кадра"



    closecon = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.70.03: Пройдено:     Сервер разорвал TCP соединение после отправки S кадра в Stopped connection (после нового TCP  соединения)"
    log(FILENAME,closecon)

