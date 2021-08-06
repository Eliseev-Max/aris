
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
def test_timeout3_autotest_5_3_2_90_8(t3_SERVER,det,IP,PORT):
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

    t3server = str (t3_SERVER)

    
   
    client.connect()

    time.sleep(t3_SERVER + det)

    if len(u_frame_checker(client)) != 0 and str(u_frame_checker(client)[-1].data.type) == "TESTFR_ACT":
        timet3act = u_frame_checker(client)[-1].timestamp/1000
        timet3con = client.events()[-2].timestamp/1000
        timet3 =int( timet3act - timet3con )
    else:
        wart3 = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.8: !Ошибка:     После таймера t3 не обнаружен TESTFR_ACT"
        log(FILENAME,wart3)
        assert len(u_frame_checker(client)) != 0 and str(u_frame_checker(client)[-1].data.type) == "TESTFR_ACT", "Проверка таймера t3"

    if t3_SERVER - 1 <= timet3 <= t3_SERVER + 1:
        t3poss = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.8: Пройдено:     Корректное срабатывание таймера t3"
        log(FILENAME,t3poss)
    else:
        result31 = str(timet3)
        t3neg = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.8: !Ошибка:     Проверка таймера t3 (Полученное значение таймера t3 ["+ result31 +" с] не соответствует заданному["+ t3server +" c])\n"
        log (FILENAME, t3neg)
        assert t3_SERVER - 1 <= timet3 <= t3_SERVER + 1, "Проверка таймера t3"
    
    
