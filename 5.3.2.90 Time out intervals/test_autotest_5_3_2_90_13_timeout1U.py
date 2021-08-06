
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

def test_timeout1U_autotest_5_3_2_90_13(t1_SERVER,t3_SERVER,det,IP,PORT):
    bufferclear(IP,PORT)
    client = rkts.Client60870(port=PORT,
                                address=IP,
                                bufferSize=1000)
    client.autoAckReachedW = True          #Sending S-frame after reaching W parameter
    client.timerT2Work = False              #Sending S-frame after t2 timeout
    client.timerT1Work = False
    client.autoAckTestFrame = False
    client.timerT3Work = False               #Sending U-frame TESTFR_Ack after the configured time period t3
    spObj = rkts.IOSinglePoint()
    client.connect()

    client.sendStartDT()
    time.sleep(0.5)
    client.sendSFrame()
    time.sleep(t3_SERVER + det)

    if str(u_frame_checker(client)[-1].data.type) == "TESTFR_ACT":
        Uframet1 = u_frame_checker(client)[-1].timestamp/1000
    else:
        assert str(u_frame_checker(client)[-1].data.type) == "TESTFR_ACT", "Проверка таймера t1 (U frame) не обнаружен TESTFR_ACT"
    client.sendIO(spObj, rkts.CauseOfTransmission.COT_ACTIVATION, 1)
    time.sleep(0.5)
    client.sendSFrame()
    time.sleep(0.5)
    client.sendTestAct()
    time.sleep(t1_SERVER + det)
    #time.sleep(40)
    conCloseTime = 0
    for ev in client.events():
        if ev.type == rkts.EventType.CONNECTION_CLOSED:
            conCloseTime = int(ev.timestamp/1000)
            result1U = conCloseTime - Uframet1
            client.disconnect()
        else: continue
    
    if conCloseTime == 0:
            Ut1err = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.13: !Ошибка:     Таймер t1 (U Frame) был сброшен кадрами I,S,U (сервер не разорвал соединение)"
            log(FILENAME,Ut1err)
            assert conCloseTime != 0, "Проверка таймера t1 (U frame)"
    
    if t1_SERVER - 1 <= result1U <= t1_SERVER + 1:
        dopt1 = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.13: Пройдено:     Отсутствует сброс таймера t1 (U Frame) кадрами I,S,U"
        log(FILENAME,dopt1)
    else:
        sresult1U = str(result1U)
        errdopt1 = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.13: !Ошибка:     (t1 U Frame) Полученное значение t1 ["+sresult1U+"] не соответствует заданному["+ t1server +" c])\n"
        log(FILENAME,errdopt1)
        assert t1_SERVER - 1 <= result1U <= t1_SERVER + 1, "Проверка таймера t1 (U frame)"
        

