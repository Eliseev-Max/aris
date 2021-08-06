# -*- coding: utf-8 -*-

import rkts
from flaky import flaky
import os, sys
import time, datetime
from arisconnector import ArisConnector, ArisTelnetConnector as tnc
from Tools.tools import *


DEFAULT_SERVER_PORT = 2404
DEFAULT_SERVER_IP = "10.1.32.253"


os.chdir(os.path.dirname(os.path.abspath(__file__)))        #Делаем каталог с исполняемым файлом текущим
FILENAME = f'{time.strftime("%Y%m%d_%H.%M")}_timeout_T1.log'
print("Файл с отчётом по выполненному автотесту '"+ FILENAME +"' будет доступен по следующему адресу:\n", os.path.dirname(os.path.abspath(__file__)))
nameOfReport = '''Проверка активного закрытия соединения при превышении значения тайм-аута t1
Отчет о результатах автоматического тестирования

'''

servParams = f"\nПараметры подключения к серверу IEC 60870-5_104:\n"\
             f"IP-адрес: {DEFAULT_SERVER_IP} \n"\
             f"TCP-порт: {DEFAULT_SERVER_PORT}\n"

servProtocolParams = """
Параметры протокола IEC 60870-5 104 для сервера:
k = 12
w = 8
t1 = 15
t2 = 10
t3 = 20

"""
c = rkts.Client60870(port=DEFAULT_SERVER_PORT, address=DEFAULT_SERVER_IP, bufferSize=1000)
p_k = str(c.paramAPCI.k)
p_w = str(c.paramAPCI.w)
p_t1 = str(c.paramAPCI.t1)
p_t2 = str(c.paramAPCI.t2)
p_t3 = str(c.paramAPCI.t3)

clientProtocolParams = f"\nПараметры протокола IEC 60870-5 104 для клиента:\n"\
                       f"\tk = {p_k}\n"\
                       f"\tw = {p_w}\n"\
                       f"\tt1 = {p_t1}\n"\
                       f"\tt2 = {p_t2}\n"\
                       f"\tt3 = {p_t3}\n"

w_off = "ОТКЛЮЧЕНА функция автоматической отправки клиентом подтверждения (APDU формата S).\n"\
        "Таймер T3 клиента отключен. \n"

header_log = (nameOfReport.center(120) + 
             f'\nВремя создания отчёта: {time.strftime("%H:%M:%S")}' +
             servParams + servProtocolParams + 
             clientProtocolParams + w_off)



def test_t1_timeout(ip, write_log, csv):

    if write_log:
        log(FILENAME, header_log)


    client = rkts.Client60870(port=DEFAULT_SERVER_PORT, address=ip, bufferSize=1000)

    client.autoAckReachedW = False          #Sending S-frame after reaching W parameter
    client.timerT2Work = False              #Sending S-frame after t2 timeout
    client.autoAckTestFrame = False          #If true test frames will be acknowledged automatic
    client.timerT3Work = False               #Sending U-frame TESTFR_Ack after the configured time period t3

    client.connect()

    try:
        assert client.isConnected, "Клиенту не удалось установить TCP-соединение с сервером"
            
    except AssertionError as err:
        repConnection = err
        print(err)
    else:
        repConnection = f'{time.strftime("%H:%M:%S")}  TCP-соединение между клиентом и сервером установлено.\n'
        print(repConnection)
        

    # Telnet. Управление сменой значений LOC.Control.Alarm
    spGenerator(ip, 1)

    client.sendStartDT()

    time.sleep(0.5)
    
    unconf_I_frames = client.unconfirmedRecvICount

    startdt = u_frame_checker(client)

    assert "STARTDT_CON" in startdt, "Клиентом не получено подтверждение STARTDT_CON"

    checkUFrames = "Клиентом был отправлен блок данных U-формата, содержащий функцию STARTDT_Act.\n"\
        "Сервером был отправлен ответ: блок данных U-формата, содержащий функцию STARTDT_Con."
    
    if write_log:
        log(FILENAME, checkUFrames)
        
    firstIFrameTime = int(client.events()[-2].timestamp/1000)

    time.sleep(16)
    
    for ev in client.events():
        if ev.type == rkts.EventType.CONNECTION_CLOSED:
            conCloseTime = int(ev.timestamp/1000)
            print(f"{exact_time(ev.timestamp)} - Активное закрытие TCP-соединения по тайм-ауту"  )
            print(f"С момента получения превого блока данных I-формата до активного закрытия прошло {conCloseTime - firstIFrameTime} с")

            client.disconnect()
        else: continue

    listOfEvents = sort_events(client)

    stringOfEvents = "".join(listOfEvents)
    eventLog = "\nЖурнал событий:\n" + stringOfEvents
    
    if write_log:
        log(FILENAME, eventLog)  

    if csv:
        events_in_csv(client)
    # client.sendStopDT()
    # client.disconnect()
    # print("{}  TCP-соединение закрыто.\n".format(time.strftime("%H:%M:%S")))
    client.connect()
    time.sleep(0.3)

    client.sendStartDT()
    time.sleep(0.3)

    client.sendSFrame(unconf_I_frames)

    client.sendStopDT()
    
    client.disconnect()

    events_in_csv(client)
