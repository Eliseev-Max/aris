# -*- coding: utf-8 -*-
import rkts
import time
import datetime
import csv
from arisconnector import ArisConnector, ArisTelnetConnector as tnc

# Функция приведения метки времени в UNIX-time к формату "ММ:СС.мС"
def exact_time(tmstmp):
    """Преобразует метку времени, полученную в unix-time в читаемый формат: ММ:СС.мС"""
    hms = tmstmp//1000
    ms = round(tmstmp%1000)
    return "\t{}.{}".format(time.strftime("%M:%S",time.localtime(hms)),ms)

# Функция отображения текущего времени в формате "ММ:СС.мС"
def get_timestamp():
    """Функция возвращает текущее время в формате: ММ:СС.мС"""
    try:
        return (f"\t+{time.strftime('%M:%S')}.{(round(datetime.datetime.now().microsecond/1000))}")
    except NameError:
        return print("Не подключены необходимые модули: time, datetime")

# Функция записи событий в лог-файл
def log(name, entry):
    with open(name,"a", encoding="utf-8") as n:
        n.write(str(entry))

# Функция генерации спорадики путём изменения значения канала LOC.Control.Alarm
def spGenerator(ip_address, switchings=6):
    """Генератор спорадики. Производит смену значений параметра LOC.Control.Alarm"""
    # Check Telnet connection
    tnConParams = {"ip" : ip_address, "port" : "23","login" : "root","pass" : "fhbc'rcg","timeout":60}
    cmd_timeout = 0.2       #Пауза между командами смены значения
    tn_obj = tnc(tnConParams)
    tn_obj.connect()
    time.sleep(1)
    cmd1 = "warehouse_set -n LOC.Control.Alarm -v 1 -q 192"
    cmd2 = "warehouse_set -n LOC.Control.Alarm -v 0 -q 192"
    sw = []    
    for cnt in range(switchings):
        tn_obj.run_command(cmd1)
        time.sleep(cmd_timeout)
        tn_obj.run_command(cmd2)
        time.sleep(cmd_timeout)
    tn_obj.disconnect()


# Функция поиска блоков данных U-формата среди всех событий
def u_frame_checker(client_object):
    """
    Функция возвращает список значений функции APCI блоков данных
    U-формата, обнаруженных в результате анализа всех событий
    приёма/передачи данных

    """
    u_frame_func = []
    try:
        for elem in client_object.events():
            if elem.type != rkts.EventType.U_FRAME:
                continue
            else:
                u_frame_func.append(str(elem.data.type))
        assert u_frame_func !=[],"Блоков данных U-формата не обнаружено"
    except AssertionError as err:
        print(err)
    finally:
        return u_frame_func


# Функция проверки подтверждения полученных сервером I-фреймов в количестве < W
def confirmation_of_W(client_obj, num_of_events, W=8, delay=0):
    """
    В функции осуществляется отправка I-фреймов серверу в количестве W
    и проверка подтверждения от сервера в виде S-фрейма.
    Возвращает список объектов блоков данных S-формата

    """

    spObj = rkts.IOSinglePoint()
    for sendingCount in range(0,W):
        client_obj.sendIO(spObj, rkts.CauseOfTransmission.COT_ACTIVATION, 1)
        time.sleep(delay)
    time.sleep(0.5)
    count_events = int(client_obj.eventsCount)
    dif = num_of_events - count_events
    recv_S_frame = []
    for number in range(dif,0,1):
        if client_obj.events()[number].type != rkts.EventType.S_FRAME:
            continue
        else:
            recv_S_frame.append(client_obj.events()[number])
    # try:
    #     assert recv_S_frame != [],"Клиентом не получено ни одного блока данных S-формата"
    #     assert len(recv_S_frame) == 1,"Клиентом получено более одного блока данных S-формата"
    # except AssertionError as err:
    #     print(err)
    return recv_S_frame


def sort_events(client_obj):
    """Функция возвращает список всех событий в их прямой последовательности"""
    list_of_events = []
    for el in client_obj.events():
        if el.type == rkts.EventType.CONNECTION_OPENED or el.type == rkts.EventType.CONNECTION_CLOSED or el.type == rkts.EventType.CONNECTION_FAILED:
            if el.type == rkts.EventType.CONNECTION_OPENED:
                connectionOpened = f"{exact_time(el.timestamp)}: TCP-соединение установлено.\n"
                list_of_events.append(connectionOpened)

            if el.type == rkts.EventType.CONNECTION_CLOSED:
                connectionClosed = f"{exact_time(el.timestamp)}: TCP-соединение прекращено. \n"
                list_of_events.append(connectionClosed)

            if el.type == rkts.EventType.CONNECTION_FAILED:
                connectionFailed = f"{exact_time(el.timestamp)}: Не удалось установить TCP-соединение между клиентом и сервером\n"
                list_of_events.append(connectionFailed)
                print(connectionFailed)
        else:
            if el.type == rkts.EventType.T1_TIMEOUT or el.type == rkts.EventType.T2_TIMEOUT or el.type == rkts.EventType.T3_TIMEOUT:
                timeoutEvent = f"{exact_time(el.timestamp)}: Зарегистрировано событие типа {el.type}\n"
                list_of_events.append(timeoutEvent)
            else:
                if el.data.isSent == True:
                    transDirection = "Клиентом отправлен блок данных формата "
                else: transDirection = "Клиентом получен блок данных формата "
                addToReport = f"{exact_time(el.timestamp)}: {transDirection} {el.type}. "
                list_of_events.append(addToReport)
                if el.type == rkts.EventType.U_FRAME:
                    u_frame = f"Тип функции: {el.data.type}.\n"
                    list_of_events.append(u_frame)
                if el.type == rkts.EventType.S_FRAME:
                    s_frame = f"Принимаемый порядковый номер: {el.data.sVal}.\n"
                    list_of_events.append(s_frame)
                if el.type == rkts.EventType.I_FRAME_PROCESS_INFO_MON_DIR or el.type == rkts.EventType.END_OF_INIT or el.type == rkts.EventType.I_FRAME_PROCESS_INFO_CONTR_DIR:
                    i_frame = f"Передаваемый порядковый номер N(S): {el.data.recvCount}; принимаемый порядковый номер N(R): {el.data.sentCount}\n"
                    list_of_events.append(i_frame)
    return list_of_events


def events_in_csv(client_obj):
    """Функция возвращает CSV-файл со всеми событиями в их прямой последовательности"""
    fieldnames = ["Метка_времени","Тип_события","Направление_передачи","Содержание"]
    list_of_events = []
    for el in client_obj.events():
        if el.type == rkts.EventType.CONNECTION_OPENED or el.type == rkts.EventType.CONNECTION_CLOSED or el.type == rkts.EventType.CONNECTION_FAILED:
            current_event = dict(Метка_времени=exact_time(el.timestamp),
                                 Тип_события=el.type,
                                 Направление_передачи=None,
                                 Содержание=None)
            list_of_events.append(current_event)
        else:
            if el.type == rkts.EventType.T1_TIMEOUT or el.type == rkts.EventType.T2_TIMEOUT or el.type == rkts.EventType.T3_TIMEOUT:
                current_event = dict(Метка_времени=exact_time(el.timestamp),
                                     Тип_события=el.type,
                                     Направление_передачи=None,
                                     Содержание=None)
                list_of_events.append(current_event)
            else:
                if el.data.isSent == True:
                    trans_dir = "Отправлено клиентом"
                else: trans_dir = "Получено клиентом"

                if el.type == rkts.EventType.U_FRAME:
                    current_event = dict(Метка_времени=exact_time(el.timestamp),
                                         Тип_события=el.type,
                                         Направление_передачи=trans_dir,
                                         Содержание=el.data.type)
                    list_of_events.append(current_event)
                if el.type == rkts.EventType.S_FRAME:
                    current_event = dict(Метка_времени=exact_time(el.timestamp),
                                         Тип_события=el.type,
                                         Направление_передачи=trans_dir,
                                         Содержание=f"S({el.data.sVal})")
                    list_of_events.append(current_event)
                if el.type == rkts.EventType.I_FRAME_PROCESS_INFO_MON_DIR or \
                    el.type == rkts.EventType.END_OF_INIT or \
                    el.type == rkts.EventType.I_FRAME_PROCESS_INFO_CONTR_DIR:
                    current_event = dict(Метка_времени=exact_time(el.timestamp),
                                         Тип_события=el.type,
                                         Направление_передачи=trans_dir,
                                         Содержание=f"N(S) = {el.data.recvCount}, N(R) = {el.data.sentCount}")
                    list_of_events.append(current_event)
    with open(f"{time.strftime('%Y%m%d_%H.%M')}_events_log.csv", "w", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, delimiter=',', fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_events:
            writer.writerow(row)