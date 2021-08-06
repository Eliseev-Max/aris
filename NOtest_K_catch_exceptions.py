# -*- coding: utf-8 -*-
"""
Тест выполняет проверку следующих положений IEC 60870-5-604:
+    ► Начальное значение порядковых номеров отправки N(S) и получения N(R) установлено равным 0
      после успешного TCP-соединения Первичной и Вторичной станций
-    ► Блок данных I-формата содержит текущие значения порядковых номеров отправки N(S) и получения N(R)
-    ► После отправки блока данных I-формата порядковый номер отправки N(S) на Первичной станции увеличился на 1
+    ► Неподтверждённые блоки данных I-формата подтверждены блоком данных S-формата от Вторичной станции
+/-    ► Порядковый номер получения N(R) подтверждает все неподтверждённые ранее блоки данных I-формата, у которых N(S) < N(R)
-    ► Первичная станция может передать неподтверждённых блоков данных I-формата не более установленного значения K,
      прежде чем остановить отправку блоков данных и ожидать подтверждения
    ► На блок данных U-формата с управляющей функцией STARTDT_ACT получен ответ STARTDT_CON
    ► На блок данных U-формата с управляющей функцией STOPDT_ACT получен ответ STOPDT_CON
"""
import rkts
from flaky import flaky
import os, sys
import time, datetime
from arisconnector import ArisConnector, ArisTelnetConnector as tnc

os.chdir(os.path.dirname(os.path.abspath(__file__)))        #Делаем каталог с исполняемым файлом текущим

REAL_SERVER_PORT_1 = 2404
REAL_SERVER_ADDR = "10.1.32.253"

def exact_time(tmstmp):
    """Преобразует метку времени, полученную в unix-time в читаемый формат: ММ:СС.мС"""
    hms = tmstmp//1000
    ms = round(tmstmp%1000)
    return "\t{}.{}".format(time.strftime("%M:%S",time.localtime(hms)),ms)

def tstamp():
    """Функция возвращает текущее время в формате: ММ:СС.мС"""
    try:
        return ("\t"+time.strftime("%M:%S")+"."+ str(round(datetime.datetime.now().microsecond/1000)))
    except NameError:
        return print("Не подключены необходимые модули: time, datetime")

def log(name, entry):
    with open(name,"a", encoding="utf-8") as n:
        n.write(str(entry))

def spGenerator(ip_address, switchings=4):
    """Генератор спорадики. Производит смену значений параметра LOC.Control.Alarm"""
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
        sw.append(time.time()*1000)
        time.sleep(cmd_timeout)
        tn_obj.run_command(cmd2)
        sw.append(time.time()*1000)
        time.sleep(cmd_timeout)
    tn_obj.disconnect()
    return sw


filename = time.strftime("%Y%m%d_%H.%M")+"_autotest_parameter_K_log.txt"
print("Файл с отчётом по выполненному автотесту '"+ filename +"' будет доступен по следующему адресу:\n", os.path.dirname(os.path.abspath(__file__)))
nameOfReport = '''Проверка количества неподтверждённых кадров I-формата, которые сервер может отправить клиенту
Отчет о результатах автоматического тестирования
'''
servParams = "\nПараметры подключения к серверу IEC 60870-5_104\nIP-адрес: " + REAL_SERVER_ADDR + "\nTCP-порт: " + str(REAL_SERVER_PORT_1)
servProtocolParams = """
Параметры протокола IEC 60870-5 104 для сервера:
k = 12
w = 8
t1 = 15
t2 = 10
t3 = 20
"""
k_server = 12
c = rkts.Client60870(port=REAL_SERVER_PORT_1, address=REAL_SERVER_ADDR, bufferSize=1000)
p_k = str(c.paramAPCI.k)
p_w = str(c.paramAPCI.w)
p_t1 = str(c.paramAPCI.t1)
p_t2 = str(c.paramAPCI.t2)
p_t3 = str(c.paramAPCI.t3)
clientProtocolParams = "\nПараметры протокола IEC 60870-5 104 для клиента:\nk = {0}\nw = {1}\nt1 = {2}\nt2 = {3}\nt3 = {4}\n".format(p_k,p_w,p_t1,p_t2,p_t3)
w_off = "ОТКЛЮЧЕНА функция автоматической отправки клиентом подтверждения (APDU формата S) после получения им от сервера W блоков данных I-формата. \n"

with open(filename,"w", encoding="utf-8") as f:
    f.write(nameOfReport + "\nВремя создания отчёта: " + time.strftime("%H:%M:%S") + servParams + servProtocolParams + clientProtocolParams + w_off)
f.close()


def test_maxNumberOfIFramesIsK():
    client = rkts.Client60870(port=REAL_SERVER_PORT_1, address=REAL_SERVER_ADDR, bufferSize=1000)
    client.autoAckReachedW = False
    client.timerT2Work = False

    try:
        client.connect()
        assert client.isConnected == True, "Не удалось установить TCP-соединение между клиентом и сервером"
        repConnection = "TCP-соединение между клиентом и сервером установлено.\n"
        print(repConnection)
    except AssertionError as err:
        repConnection = str(err)
        print(err)

############__Telnet. Управление сменой значений LOC.Control.Alarm__#########
    switchingTime = spGenerator(REAL_SERVER_ADDR)
    time.sleep(5)

    client.sendStartDT()
    time.sleep(1)

#### Проверка обмена блоками данных STARTDT_ACT -> <- STARTDT_CON ####
    assert client.events()[1].type == rkts.EventType.U_FRAME, "Клиентом не отправлен блок данных U-формата (STARTDT_ACT)"
    assert str(client.events()[1].data.type) == "STARTDT_ACT", "Блок данных U-формата НЕ содержит функцию STARTDT_ACT"
    assert client.events()[2].type == rkts.EventType.U_FRAME, "Клиентом не было получено подтверждение от сервера (STARTDT_CON)"
    assert str(client.events()[2].data.type) == "STARTDT_CON", "Блок данных U-формата НЕ содержит подтверждение STARTDT_CON"

    unconfRecIFrames_0 = int(client.unconfirmedRecvICount)
    try:
        assert client.events()[3].type == rkts.EventType.I_FRAME_PROCESS_INFO_MON_DIR or el.type == rkts.EventType.END_OF_INIT,"Отправлен блок данных не I-формата"
        assert int(client.events()[3].data.recvCount) == 0,"Начальное значение передаваемого порядкового номера блока данных не равно 0"
        assert int(client.events()[3].data.sentCount) == 0,"Начальное значение принимаемого порядкового номера блока данных не равно 0"
    except AssertionError:
        assertError = "Ошибка при передаче первого блока данных I-формата"
        print(assertError)
        reportBuffer = "На момент начала передачи данных в буфере сервера содержится {} неподтверждённых блоков данных I-формата".format(unconfRecIFrames_0)
        print(reportBuffer)

    try:
        assert client.events()[3].type == rkts.EventType.I_FRAME_PROCESS_INFO_MON_DIR or el.type == rkts.EventType.END_OF_INIT,"Отправлен блок данных не I-формата"
        assert int(client.events()[3].data.recvCount) == 0,"Начальное значение передаваемого порядкового номера блока данных не равно 0"
        assert int(client.events()[3].data.sentCount) == 0,"Начальное значение принимаемого порядкового номера блока данных не равно 0"
    except AssertionError:
            print("Ошибка при передаче первого блока данных I-формата")

    unconfRecIFrames_1 = int(client.unconfirmedRecvICount)      #12
    #print(unconfRecIFrames_1)
    #print(len(switchingTime))
    try:
        assert int(unconfRecIFrames_1) == k_server,"Количество неподтверждённых блоков данных I-формата не соответствует K"
        assert int(client.unconfirmedRecvICount) < len(switchingTime),"Сервер не остановил передачу при достижении K блоков I-формата"
    except AssertionError as err:
        print(err)
    client.sendSFrame(unconfRecIFrames_1)
    print("Отправили S-frame, подтверждающий {} блоков данных I-формата".format(unconfRecIFrames_1))
    time.sleep(2)
    print("Количество неподтверждённых блоков данных после отправки S-frame: {}".format(client.unconfirmedRecvICount))
    client.sendSFrame(unconfRecIFrames_1)
    print("Засласли S-frame, подтверждающий {} блоков данных I-формата".format(unconfRecIFrames_1))
    time.sleep(2)
    unconfRecIFrames_2 = int(client.unconfirmedRecvICount)
    print("Количество неподтверждённых блоков данных: {}".format(unconfRecIFrames_2,))
    client.sendSFrame(unconfRecIFrames_2)
    print("Засласли S-frame, подтверждающий реальное количество неподтверждённых блоков данных")
    time.sleep(1)
    print("А теперь количество неподтверждённых блоков данных: {}".format(client.unconfirmedRecvICount))
    client.sendStopDT()
    time.sleep(1)
    assert client.events()[-2].type == rkts.EventType.U_FRAME, "Клиентом не отправлен блок данных U-формата (STOPDT_ACT)"
    assert client.events()[-1].type == rkts.EventType.U_FRAME, "Клиентом не было получено подтверждение от сервера (STOPDT_CON)"
    client.disconnect()

#########################__Сортировка событий по типам с указанием метки времени__#########################
    listOfEvents = []

    for el in client.events():
        if el.type == rkts.EventType.CONNECTION_OPENED or el.type == rkts.EventType.CONNECTION_CLOSED or el.type == rkts.EventType.CONNECTION_FAILED:
            if el.type == rkts.EventType.CONNECTION_OPENED:
                connectionOpened = "{}: TCP-соединение установлено.\n".format(exact_time(el.timestamp))
                listOfEvents.append(connectionOpened)

            if el.type == rkts.EventType.CONNECTION_CLOSED:
                connectionClosed = "{}: TCP-соединение прекращено. \n".format(exact_time(el.timestamp))
                listOfEvents.append(connectionClosed)

            if el.type == rkts.EventType.CONNECTION_FAILED:
                connectionFailed = "{}: Не удалось установить TCP-соединение между клиентом и сервером\n".format(exact_time(el.timestamp))
                listOfEvents.append(connectionFailed)
                print(connectionFailed)
        else:
            if el.type == rkts.EventType.T1_TIMEOUT or el.type == rkts.EventType.T2_TIMEOUT or el.type == rkts.EventType.T3_TIMEOUT:
                timeoutEvent = ("{}: Зарегистрировано событие типа {}\n".format(exact_time(el.timestamp), el.type))
                listOfEvents.append(timeoutEvent)
            else:
                if el.data.isSent == True:
                    transDirection = "Клиентом отправлен блок данных формата "
                else: transDirection = "Клиентом получен блок данных формата "
                addToReport = "{}: {} {}. ".format(exact_time(el.timestamp), transDirection, el.type)
                listOfEvents.append(addToReport)
                if el.type == rkts.EventType.U_FRAME:
                    u_frame = "Тип функции: {}.\n".format(el.data.type)
                    listOfEvents.append(u_frame)
                if el.type == rkts.EventType.S_FRAME:
                    s_frame = "Количество подтверждённых блоков данных I-формата: {}.\n".format(el.data.sVal)
                    listOfEvents.append(s_frame)
                if el.type == rkts.EventType.I_FRAME_PROCESS_INFO_MON_DIR or el.type == rkts.EventType.END_OF_INIT:
                    i_frame = "Передаваемый порядковый номер N(S): {}; принимаемый порядковый номер N(R): {}\n".format(el.data.recvCount, el.data.sentCount)
                    listOfEvents.append(i_frame)
                                                                        
                if el.type == rkts.EventType.I_FRAME_PROCESS_INFO_CONTR_DIR:
                    i_frame_contr = "Data: cmd {} with type {} sent {}".format(el.data.cmd, el.data.cmd.type, el.data.isSent)
                    listOfEvents.append(i_frame_contr)

####################################################################
    stringOfEvents = "".join(listOfEvents)
    log(filename, stringOfEvents)

# test_maxNumberOfIFramesIsK()

print("Отчёт сформирован в папке ", os.path.dirname(os.path.abspath(__file__)))
