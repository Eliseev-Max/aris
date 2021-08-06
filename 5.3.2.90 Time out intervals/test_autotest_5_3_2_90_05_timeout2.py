
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

def test_timeout2_autotest_5_3_2_90_5(t2_SERVER,t1_SERVER,IP,PORT):
    t2server = str (t2_SERVER)

    client = rkts.Client60870(port=PORT,
                              address=IP,
                              bufferSize=1000)
    client.autoAckReachedW = True          #Sending S-frame after reaching W parameter
    client.timerT2Work = False              #Sending S-frame after t2 timeout
    client.timerT1Work = False
    client.autoAckTestFrame = False
    client.timerT3Work = False               #Sending U-frame TESTFR_Ack after the configured time period t3
    
    spObj = rkts.IOSinglePoint()

### STEP 2. Проверка таймера t2
    client.connect()
    time.sleep(0.3)


    client.sendStartDT()
    time.sleep(0.3)

    client.sendIO(spObj, rkts.CauseOfTransmission.COT_ACTIVATION, 1)
    firstIframet2 = int(client.events()[-1].timestamp/1000)
    time.sleep(0.5*t2_SERVER)
    client.sendIO(spObj, rkts.CauseOfTransmission.COT_ACTIVATION, 1)
    tweIframet2 = int(client.events()[-1].timestamp/1000)
    time.sleep(0.5*t2_SERVER)
    client.sendIO(spObj, rkts.CauseOfTransmission.COT_ACTIVATION, 1)
    thIframet2 = int(client.events()[-1].timestamp/1000)
    time.sleep(t1_SERVER)

    count_events = int(client.eventsCount)
    recv_S_frame = []
    for num in range(0,count_events,1):
        if client.events()[num].type == rkts.EventType.S_FRAME:
            recv_S_frame.append(client.events()[num])

    if len(recv_S_frame) == 0:
        errS = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.5: !Ошибка:     Ни один S кадр не был получен клиентом"
        log(FILENAME,errS)
        assert recv_S_frame == [], "Проверка таймера t2"
    else:
        numSframe = int(recv_S_frame[0].data.sVal)
        if numSframe >= 1:
            Sframe1 = int(recv_S_frame[0].timestamp/1000)
            resultt2 = Sframe1 - firstIframet2
        else:
            stnumSframe = str(numSframe)
            errnumS ="\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.5: !Ошибка:     После ожидания таймера t2 получен некорректный S("+stnumSframe+") кадр"
            log(FILENAME,errnumS)
            assert numSframe >= 1, "Проверка таймера t2"
    
    valSframe = int(recv_S_frame[-1].data.sVal)

    if valSframe == 3:
        Sframefin = int(recv_S_frame[-1].timestamp/1000)
        resultS = Sframefin - thIframet2
    else:
        errSframefin = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.5: !Ошибка:     За время t1 не были подтверждены все отправленные I кадры"
        log(FILENAME,errSframefin)
        assert valSframe == 3, "Проверка таймера t2"

    if resultt2 > t1_SERVER - 1:
        errtimeS = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.5: !Ошибка:     Кадр S, который подтвердил все I кадры пришел позже чем сработал таймер t1"
        log(FILENAME,errtimeS)
        assert resultt2 > t1_SERVER - 1, "Проверка таймера t2"

    
    if t2_SERVER - 1 <= resultt2 <= t2_SERVER + 1:
        post2 = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.5: Пройдено:     Корректное срабатывание таймера t2, все отправленные I кадры подтверждены"
        log(FILENAME,post2)
    else:
        rest2 = str(resultt2)
        negt2 = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.2.90.5: !Ошибка:     Полученное значение таймера t2 ["+ rest2+"] не соответствует заданному ["+t2server+"]"
        log (FILENAME,negt2)
        assert t2_SERVER - 1 <= resultt2 <= t2_SERVER + 1, "Проверка таймера t2"
    
    