# -*- coding: utf-8 -*-
import rkts
import time
import datetime
import csv
import telnetlib
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


# Функция начального значения канала через TelNet
def telnet_checker():
    ip = '10.1.31.10'
    tn = telnetlib.Telnet(ip)

    to_username = tn.read_until(b'login:')
    tn.write(b'root\n')
    to_pwd = tn.read_until(b'Password')
    tn.write(b"fhbc'rcg\n")

    tn.read_until(b'#')                 #Подключение по Telnet и авторизация выполнены


    tn.write(b'warehouse_view LOC.quality_test.AI-663\r\n')
    data = ''
    while data.find('0638') == -1:
        data = tn.read_very_eager().decode('utf-8')

    value = " 0 " in data

    tn.close()

    return value


## Функция очистки буффера
def bufferclear(IP,PORT):
    type_I_frame = (rkts.EventType.I_FRAME_PROCESS_INFO_MON_DIR,
                    rkts.EventType.END_OF_INIT,
                    rkts.EventType.I_FRAME_PROCESS_INFO_CONTR_DIR)

   
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

    client.disconnect()


def specindicationgen(ip_address, vchel1,vchel2,val1,val2):

    tnConParams = {"ip" : ip_address, "port" : "23","login" : "root","pass" : "fhbc'rcg","timeout":60}
    
    tn_obj = tnc(tnConParams)
    tn_obj.connect()
    time.sleep(0.5)  
    cmd1 = "warehouse_set -n LOC.quality_test.AI-"+str(vchel1)+" -v"+ str(val1) +" -q 192"
    cmd2 = "warehouse_set -n LOC.quality_test.AI-"+str(vchel2)+" -v"+ str(val2) +" -q 192"
    tn_obj.run_command(cmd1)
    time.sleep(0.1)
    tn_obj.run_command(cmd2)
    tn_obj.disconnect

def indicationGen(ip_address,vchel,value,delay=0):
    tnConParams = {"ip" : ip_address, "port" : "23","login" : "root","pass" : "fhbc'rcg","timeout":60}
    
    tn_obj = tnc(tnConParams)
    tn_obj.connect()
    time.sleep(0.5)
    
    t = 0
    for t in range(0,len(value),1):
        a = str(value[t])
        cmd = "warehouse_set -n LOC.quality_test.AI-"+str(vchel)+" -v"+ a +" -q 192"
        tn_obj.run_command(cmd)
        time.sleep(delay)
        time.sleep(0.1)          #Пауза между командами 

    tn_obj.disconnect()


# Функция генерации спорадики путём изменения значения канала LOC.quality_test.AI-663
def spGenerator(ip_address, cvalue, pol, delay = 0):
    tnConParams = {"ip" : ip_address, "port" : "23","login" : "root","pass" : "fhbc'rcg","timeout":60}
         
    tn_obj = tnc(tnConParams)
    tn_obj.connect()
    time.sleep(0.5)

    if cvalue == True:
        per = 1
#      z = pol + 1
        z = pol
    else:
        per = 0
#        z = pol
        z = pol - 1
     
    for t in range(per,z):
        a = str(t)
        cmd = "warehouse_set -n LOC.quality_test.AI-663 -v"+ a +" -q 192"
        tn_obj.run_command(cmd)
        time.sleep(delay)
        time.sleep(0.1)          #Пауза между командами 
    sz = str(z)
    tn_obj.run_command("warehouse_set -n LOC.quality_test.AI-663 -v"+ sz +" -q 192")

    tn_obj.disconnect()

def I_frame_checker_cmd(client_object):
    ### Возвращает список с командами от сервера
    I_frame_rec = []
    try:
        for elem in client_object.events():
            if elem.type != rkts.EventType.I_FRAME_SYSTEM_INFO_CONTR_DIR:
                continue
            else:
                I_frame_rec.append(elem)
                assert I_frame_rec !=[],"Блоков данных I-формата не обнаружено"
    except AssertionError as err:
        print(err)
    finally:
        return I_frame_rec

def I_frame_checker_Spont(client_object,ioa,type,spont,adr):
    """
        Возвращает ASDU I  кадров с причиной передачи <3> Спорадика
    """
    I_frame_func = []
    I_frame_rec = []
    try:
        for elem in client_object.events():
            if elem.type != rkts.EventType.I_FRAME_PROCESS_INFO_MON_DIR:
                continue
            else:
                if (str(elem.data.asdu.type) == type) and(elem.data.asdu.commonAddress == adr): 
                    I_frame_func.append(elem)
                assert I_frame_func !=[],"Блоков данных I-формата не обнаружено"
    
        for f in I_frame_func:
            for x in range(0,f.data.asdu.elementsCount(),1):
                if (f.data.asdu.causeOfTransmission == spont) and (f.data.asdu.at(x).ioa == ioa):
                    I_frame_rec.append(f.data.asdu.at(x))
  

    except AssertionError as err:
        print(err)
    finally:
        return I_frame_rec

def I_frame_checker_inrogen(client_object,ioa,type,inrogen,adr):
## Возвращает ASDU I  кадров с причиной передачи <20> ответ на general INTERROGATED
    I_frame_func = []
    I_frame_rec = []
    try:
        for elem in client_object.events():
            if elem.type != rkts.EventType.I_FRAME_PROCESS_INFO_MON_DIR:
                continue
            else:
                if (str(elem.data.asdu.type) == type) and (elem.data.asdu.commonAddress == adr): 
                    I_frame_func.append(elem)
                assert I_frame_func !=[],"Блоков данных I-формата не обнаружено"
    
        for f in I_frame_func:
            for x in range(0,f.data.asdu.elementsCount(),1):
                if (f.data.asdu.causeOfTransmission == inrogen) and (f.data.asdu.at(x).ioa == ioa):
                    I_frame_rec.append(f.data.asdu.at(x))
  

    except AssertionError as err:
        print(err)
    finally:
        return I_frame_rec

def I_frame_checker_requst(client_object,ioa,type,inquiry,adr):
## Возвращает ASDU I  кадров с причиной передачи <5> ответ на readcommand
    I_frame_func = []
    I_frame_rec = []
    try:
        for elem in client_object.events():
            if elem.type != rkts.EventType.I_FRAME_PROCESS_INFO_MON_DIR:
                continue
            else:
                if (str(elem.data.asdu.type) == type) and(elem.data.asdu.commonAddress == adr): 
                    I_frame_func.append(elem)
                assert I_frame_func !=[],"Блоков данных I-формата не обнаружено"
    
        for f in I_frame_func:
            for x in range(0,f.data.asdu.elementsCount(),1):
                if (f.data.asdu.causeOfTransmission == inquiry) and (f.data.asdu.at(x).ioa == ioa):
                    I_frame_rec.append(f.data.asdu.at(x))
  

    except AssertionError as err:
        print(err)
    finally:
        return I_frame_rec

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
                u_frame_func.append(elem)
        assert u_frame_func !=[],"Блоков данных U-формата не обнаружено"
    except AssertionError as err:
        print(err)
    finally:
        return u_frame_func


# Функция проверки подтверждения полученных сервером I-фреймов в количестве < W
#def confirmation_of_W(client_obj, num_of_events, W=8, delay=0.3):
 #   """Функция осуществляет отправку I-фреймов серверу и проверяет,
  #  поступило ли от сервера подтверждение в виде S-фрейма"""
   # spObj = rkts.IOSinglePoint()
 

    #time.sleep(0.5)
   # count_events = int(client_obj.eventsCount)
    #dif = num_of_events - count_events
    
    #for number in range(dif,0,1):
    #    if client_obj.events()[number].type != rkts.EventType.S_FRAME:
     #       continue
      #  else:
       #     recv_S_frame = int(client_obj.events()[number].data.sVal)

   # return recv_S_frame


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