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




def test_timeout0_preparation(t1_SERVER,det,IP,PORT,t2_SERVER,t3_SERVER):
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    FILENAME = "Timeout_log.txt"
    print(f"Файл с отчётом по выполненному автотесту \"{FILENAME}\" будет доступен "\
        f"по следующему адресу:\n {os.path.dirname(os.path.abspath(__file__))}")
    nameOfReport = "Отчет о результатах выполнения автотеста 5.3.2.90 Time out intervals\n"
    servParams = f"\nПараметры подключения к серверу IEC 60870-5_104:\n\tIP-адрес: "\
                    f"{IP}\n\tTCP-порт: {PORT}"
    KServer = str(K_SERVER)
    WServer = str(W_SERVER)
    t1server = str (t1_SERVER)
    t2server = str (t2_SERVER)
    t3server = str (t3_SERVER)
    servProtocolParams = """
Параметры протокола IEC 60870-5 104 для сервера:
t1 = """ + t1server +""" c
t2 = """ + t2server +""" c
t3 = """ + t3server +""" c
"""
    c = rkts.Client60870(port=PORT,
                        address=IP,
                        bufferSize=1000)
    p_k = str(c.paramAPCI.k)
    p_w = str(c.paramAPCI.w)
    p_t1 = str(c.paramAPCI.t1)
    p_t2 = str(c.paramAPCI.t2)
    p_t3 = str(c.paramAPCI.t3)
    clientProtocolParams = f"\nПараметры протокола IEC 60870-5 104 для клиента:\n" + "(Отключен) t1 = " + p_t1 + " c\n(Отключен) t2 = " + p_t2 + " c\n(Отключен) t3 = " + p_t3 + " c\nK = " + p_k + "\nW = " + p_w

    header_log = (nameOfReport + "\nВремя создания отчёта: " + time.strftime("%H:%M:%S")
                + servParams + servProtocolParams + "K = " + KServer + "\nW = " + WServer + clientProtocolParams)
    if LOGGING:
        log(FILENAME, header_log)

    repConnection = "\n\nTCP-соединение между клиентом и сервером установлено.\n"
    log (FILENAME,repConnection)

    stagesHead = "\nЭтапы прохождения теста:\n"
    if LOGGING:
        log(FILENAME, stagesHead)

    type_I_frame = (rkts.EventType.I_FRAME_PROCESS_INFO_MON_DIR,
                    rkts.EventType.END_OF_INIT,
                    rkts.EventType.I_FRAME_PROCESS_INFO_CONTR_DIR)

    t1server = str (t1_SERVER)
   
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
    client.sendStartDT()
    time.sleep (2)

    client.sendSFrame()


