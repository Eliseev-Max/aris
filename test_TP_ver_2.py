# -*- coding: utf-8 -*-
"""
Тест выполняет проверку следующих положений IEC 60870-5-604:
+    ► Начальное значение порядковых номеров отправки N(S) и получения N(R) \
        установлено равным 0 после успешного TCP-соединения Первичной и Вторичной станций
+    ► Блок данных I-формата содержит текущие значения порядковых номеров \
        отправки N(S) и получения N(R)
+    ► После отправки блока данных I-формата порядковый номер отправки N(S) \
     на Первичной станции увеличился на 1
+    ► Неподтверждённые блоки данных I-формата подтверждены блоком данных S-формата/I-формата от Вторичной станции
+    ► Порядковый номер получения N(R) подтверждает все неподтверждённые ранее блоки данных I-формата, у которых N(S) < N(R)
+    ► Первичная станция может передать неподтверждённых блоков данных I-формата не более установленного значения K,
      прежде чем остановить отправку блоков данных и ожидать подтверждения
+    ► На блок данных U-формата с управляющей функцией STARTDT_ACT получен ответ STARTDT_CON
+    ► На блок данных U-формата с управляющей функцией STOPDT_ACT получен ответ STOPDT_CON
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
REAL_SERVER_PORT = 2404
# REAL_SERVER_ADDR = "10.1.31.10"
REAL_SERVER_ADDR = "10.1.32.253"
K_SERVER = 12

type_I_frame = (rkts.EventType.I_FRAME_PROCESS_INFO_MON_DIR,
                rkts.EventType.END_OF_INIT,
                rkts.EventType.I_FRAME_PROCESS_INFO_CONTR_DIR)
#Делаем каталог с исполняемым файлом текущим
os.chdir(os.path.dirname(os.path.abspath(__file__)))
FILENAME = time.strftime("%Y%m%d_%H.%M")+"_TransmissionProc_log.txt"
print(f"Файл с отчётом по выполненному автотесту \"{FILENAME}\" будет доступен "\
        f"по следующему адресу:\n {os.path.dirname(os.path.abspath(__file__))}")
nameOfReport = "Проверка процедуры передачи информации между клиентом и сервером\n"\
                "Отчет о результатах автоматического тестирования"

servParams = f"\nПараметры подключения к серверу IEC 60870-5_104:\n\tIP-адрес: "\
                f"{REAL_SERVER_ADDR}\n\tTCP-порт: {REAL_SERVER_PORT}"
servProtocolParams = """
Параметры протокола IEC 60870-5 104 для сервера:
    k = 12
    w = 8
    t1 = 15
    t2 = 10
    t3 = 20
"""
c = rkts.Client60870(port=REAL_SERVER_PORT,
                    address=REAL_SERVER_ADDR,
                    bufferSize=1000)
p_k = str(c.paramAPCI.k)
p_w = str(c.paramAPCI.w)
p_t1 = str(c.paramAPCI.t1)
p_t2 = str(c.paramAPCI.t2)
p_t3 = str(c.paramAPCI.t3)
clientProtocolParams = f"\nПараметры протокола IEC 60870-5 104 для клиента:\n\t"\
                        f"k = {p_k}\n\tw = {p_w}\n\tt1 = {p_t1}\n\tt2 = {p_t2}\n\tt3 = {p_t3}\n"
W_OFF = "ОТКЛЮЧЕНА функция автоматической отправки клиентом подтверждения " \
        "(APDU формата S) после получения им от сервера не более W блоков данных I-формата. \n"
header_log = (nameOfReport.center(115) + "\nВремя создания отчёта: " + time.strftime("%H:%M:%S")
            + servParams + servProtocolParams + clientProtocolParams + W_OFF)
if LOGGING:
    log(FILENAME, header_log)
#@flaky()
def test_transmission():
    """В функции создаётся виртуальный клиент, на сервере запускается генерация \
    спорадики, выполняются тесты из раздела № 5.3.2.90 технической спецификации \
    IEC 60870-5-604. Результаты выполнения тестов и хронология событий, относящихся \
    к процедуре передачи данных между клиентом и сервером, записываются в лог-файл
    """
    client = rkts.Client60870(port=REAL_SERVER_PORT,
                              address=REAL_SERVER_ADDR,
                              bufferSize=1000)
    client.autoAckReachedW = False
    client.timerT2Work = False
    spObj = rkts.IOSinglePoint()
    client.connect()
# Проверка TCP-соединения
    assert client.isConnected == True, "Не удалось установить TCP-соединение между \
            клиентом и сервером"
    repConnection = "TCP-соединение между клиентом и сервером установлено.\n"
    print(repConnection)

# Telnet. Управление сменой значений LOC.Control.Alarm
    spGenerator(REAL_SERVER_ADDR, switchings=14)
    print("Генерация спорадики запущена. Команда на старт передачи данных не отправлена клиентом")

    stagesHead = "\nЭтапы прохождения теста:\n"

    if LOGGING:
        log(FILENAME, stagesHead)
    
    count_of_events = int(client.eventsCount)
    cptrans = "\nПередача I frames при TCP соединении без STARTDT"

    if LOGGING:
        log(FILENAME,cptrans)
    assert count_of_events == 1,"Непредвиденное событие до старта передачи данных"

    passed = "     Пройдено\n"
    if LOGGING:
        log(FILENAME,passed)
    
    client.sendStartDT()
    print("Клиентом отправлена команда на старт передачи данных")
    time.sleep(0.5)
    print(f"Количество принятых клиентом блоков данных "\
            f"I-формата после получения подтверждения от "\
                f"сервера: {client.unconfirmedRecvICount}")

# Проверка обмена блоками данных STARTDT_ACT -> <- STARTDT_CON
    startdt = u_frame_checker(client)
    checkSTARTDT = "Ответ сервера на STARTDT_act"
    if LOGGING:
        log(FILENAME, checkSTARTDT)
    unconfRecIFrames_0 = int(client.unconfirmedRecvICount)    
    assert "STARTDT_ACT" in startdt, "Блок данных U-формата НЕ содержит "\
            "функцию STARTDT_ACT"
    assert "STARTDT_CON" in startdt, "Блок данных U-формата НЕ содержит "\
            "подтверждение STARTDT_CON"
    if LOGGING:
        log(FILENAME,passed)

# Вывод сообщений об обмене U-фреймами STARTDT (Act) (Con)
    startdt_sent = f"Клиентом отправлен блок данных U-формата, "\
                    f"содержащий функцию {client.events()[1].data.type}\n"
    startdt_conf_rcvd = f"Клиентом получено подтверждение (блок данных U-формата "\
            f"с функцией {client.events()[2].data.type})\n"
    print(f"{exact_time(client.events()[1].timestamp)} {startdt_sent}")
    print(f"{exact_time(client.events()[2].timestamp)}  {startdt_conf_rcvd}")
    


# Проверка доставки блоков данных I-формата клиенту
    assert unconfRecIFrames_0 > 0,"Клиент не получил ни одного блока данных I-формата"

# Проверяем, что APDU блока данных соответствует I-формату
    assert client.events()[3].type in type_I_frame,"После получения подтверждения подтверждения от "\
            "сервера (STARTDT_Con) клиенту поступил блок данных не I-формата"

# Проверяем, что начальные значения передаваемого N(S) и принимаемого N(R) порядковых
# номеров установлены равными 0
    seq_numbers_first_I = "Установка порядковых номеров N(S) и N(R)"\
            " после нового TCP соединения"
    if LOGGING:
        log(FILENAME, seq_numbers_first_I)    
    assert int(client.events()[3].data.recvCount) == 0,"Начальное значение передаваемого "\
            "порядкового номера блока данных не равно 0"
    assert int(client.events()[3].data.sentCount) == 0,"Начальное значение принимаемого "\
            "порядкового номера блока данных не равно 0"
    if LOGGING:
        log(FILENAME,passed)


#### Проверяем, что количество блоков данных I-формата соответствует значению K сервера
    log_check_K = "Параметр К"
    if LOGGING:
        log(FILENAME,log_check_K)
    assert int(client.unconfirmedRecvICount) == K_SERVER,"Количество неподтверждённых блоков данных I-формата не соответствует K"
    unconfRecIFrames_1 = int(client.unconfirmedRecvICount)
    if LOGGING:
        log(FILENAME,passed)


#### Создаём список, содержащий передаваемые порядковые номера I-фреймов
    sent_seq_numbers = []
    recv_seq_numbers = []

    for event in client.events():
        if event.type in type_I_frame:
            sent_seq_numbers.append(int(event.data.recvCount))
            recv_seq_numbers.append(int(event.data.sentCount))
        else: continue

    recv_seq_nun_as_string = set(recv_seq_numbers)

    # Проверяем инкрементацию N(S) и N(R)
    assert sent_seq_numbers == list(range(K_SERVER)),"Нарушена последовательность порядковых номеров передаваемых кадров"
    assert recv_seq_nun_as_string == set([0])
#    assert sendSeqNumbers == list(range(11)),"Нарушена последовательность порядковых номеров передаваемых кадров"


    # Отправляем серверу первый S-фрейм, который подтвердит K I-фреймов
    client.sendSFrame(unconfRecIFrames_1)       
    print(f"Отправили S-frame, подтверждающий {unconfRecIFrames_1} блоков данных I-формата")
    time.sleep(1)
    answ_s_frame = "Подтверждение кадром S"
    if LOGGING:
        log(FILENAME,answ_s_frame)    
    assert int(client.unconfirmedRecvICount)>unconfRecIFrames_1, "Сервер не совершал отправку блоков данных I-формата после подтверждения"
    
    if LOGGING:
        log(FILENAME,passed)

    client.sendSFrame(unconfRecIFrames_1)       # Отправили неподтверждающий S-фрейм
    time.sleep(0.5)
    unconfRecIFrames_2 = int(client.unconfirmedRecvICount)
    print(f"Отправили S-frame с порядковым номером {unconfRecIFrames_1} вместо подтверждающего порядкового номера {unconfRecIFrames_2}")
    time.sleep(0.5)

    
    # Проверка действия Сервера при отправке ему принимаемого порядкового номера N(R)<N(S)
    senreclas = "N(R) < N(S)"
    if LOGGING:
        log(FILENAME,senreclas)   
 
    assert client.events()[-1].type == rkts.EventType.S_FRAME,"Непредвиденное получение клиентом блококв данных I-формата. "
    fakeConfNumber = int(unconfRecIFrames_1) + 2
    client.sendSFrame(fakeConfNumber)       # Посмотреть, сколько поступило I-фреймов
    num_of_events_1 = int(client.eventsCount)
    time.sleep(0.5)
    num_of_events_2 = int(client.eventsCount)

    assert (num_of_events_2 - num_of_events_1) == 2, "Ошибка количества поступивших неподтверждённых блоков данных!"
    assert client.events()[-2].type in type_I_frame, "Проверка подтверждения двух блоков данных I-формата не пройдена"
    assert client.events()[-1].type in type_I_frame, "Проверка подтверждения двух блоков данных I-формата не пройдена"
    if LOGGING:
        log(FILENAME,passed)

    client.sendIO(spObj, rkts.CauseOfTransmission.COT_ACTIVATION, 1)
    print(f"Клиентом отправлен блок данных I-формата, содержащий функцию {spObj.type}")
    eventsWithSentIFrame = int(client.eventsCount)

    time.sleep(0.8)
    eventsAfterSentIFrame = int(client.eventsCount)

    answIframe = "Подтверждение кадром I"
    if LOGGING:
        log(FILENAME,answIframe)

    assert eventsAfterSentIFrame > eventsWithSentIFrame,"Отсутствуют неподтверждённые блоки данных I-формата"
    if LOGGING:
        log(FILENAME,passed)
    
    dif = eventsWithSentIFrame - eventsAfterSentIFrame
    
    incrementOk = "Последовательность порядковых номеров N(S) и N(R)"
    if LOGGING:
        log(FILENAME, incrementOk)
    for e in range(dif,0,1):
        assert client.events()[e].data.isSent == False, "Блок данных отправлен ошибочно!"
        assert client.events()[e].type in type_I_frame,"Один из полученных блоков данных после подтверждения двух \
                                                        I-фреймов оказался не блоком данных I-формата!!!"
        assert client.events()[e].data.sentCount == 1,"Ошибка инкрементирования принимаемого \
                                                        порядкового номера сервера"
    if LOGGING:
        log(FILENAME,passed)    

    
    received_S = confirmation_of_W(client, eventsAfterSentIFrame)
    print(f"Количество поступивших от сервера S-фреймов = {len(received_S)}")

    paramW = "Параметр W"
    if LOGGING:
        log(FILENAME,paramW) 
       
    assert len(received_S) == 1,"Отправленные клиентом I-фреймы не подтверждены"
    cur_count_of_events = int(client.eventsCount)
    recv_S_frame = confirmation_of_W(client,cur_count_of_events, delay=0.7)
    print(f"Количество поступивших от сервера S-фреймов = {len(recv_S_frame)}")
    assert len(recv_S_frame) != 0,"Отправленные во второй раз клиентом I-фреймы не подтверждены"
    assert len(recv_S_frame) < 2,"От сервера поступило 2 подтверждения вместо одного"
    if LOGGING:
        log(FILENAME,passed)
    
    time.sleep(1)
    client.sendStopDT()
    time.sleep(0.5)
    stopdt = u_frame_checker(client)
    assert "STOPDT_ACT" in stopdt,"Клиентом не отправлена команда прекращения передачи данных (STOPDT_Act)"
    assert "STOPDT_CON" in stopdt,"Клиентом не получено подтверждение прекращения передачи данных (STOPDT_Con)"
    client.disconnect()
# Сортировка событий по типам с указанием метки времени
    # listOfEvents = sort_events(client)
    # stringOfEvents = "".join(listOfEvents)
    # eventLog = "\nЖурнал событий:\n" + stringOfEvents
    # if LOGGING:
    #     log(FILENAME, eventLog)
    events_in_csv(client)

print("Тест пройден успешно")
print("Отчёт сформирован в папке ", os.path.dirname(os.path.abspath(__file__)))
