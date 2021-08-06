
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

def test_timeout3_autotest_5_3_2_90_9(t3_SERVER,det,IP,PORT):
    ## Инициализация клиента для тестов time out t3 и time out t1 (U frame)
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
    time.sleep(0.5*t3_SERVER)

    client.sendTestAct()
    time.sleep(0.5*t3_SERVER + det)

    testfr = u_frame_checker(client)
    
    if str(testfr[-1].data.type) == "TESTFR_CON":
        post3 = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.9: Пройдено:     Сброс таймера t3 U кадром"
        log(FILENAME,post3)
    else:
        if len(testfr) == 2:
            negt3 = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.9: !Ошибка:     Таймер t3 не был сброшен U кадром"
            log(FILENAME,negt3)
            assert len(testfr) == 3, "Проверка таймера t3, сброс таймера U кадром"
        conframe = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.9: !Ошибка:     После отправки команды TESTFR_ACT клиентом не получен TESTFR_CON"
        log(FILENAME,conframe)
        assert str(testfr[-1].data.type) == "TESTFR_CON", "Проверка таймера t3, сброс таймера U кадром"

    
