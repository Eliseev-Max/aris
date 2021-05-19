# -*- coding: utf-8 -*-

import rkts
import os
import time
import datetime
from arisconnector import ArisTelnetConnector as tnc
from Tools.tools import *


# Параметры сервера
REAL_SERVER_PORT = 2404
DEFAULT_SERVER_IP = "10.1.32.253"

type_I_frame = (
                rkts.EventType.I_FRAME_PROCESS_INFO_MON_DIR,
                rkts.EventType.END_OF_INIT,
                rkts.EventType.I_FRAME_PROCESS_INFO_CONTR_DIR
)

#Делаем каталог с исполняемым файлом текущим
os.chdir(os.path.dirname(os.path.abspath(__file__)))

FILENAME = f'{time.strftime("%Y%m%d_%H.%M")}_TransmissionProc.log'

print(f"Файл с отчётом по выполненному автотесту \"{FILENAME}\" будет доступен "\
        f"по следующему адресу:\n {os.path.dirname(os.path.abspath(__file__))}")
nameOfReport = "Проверка процедуры передачи информации между клиентом и сервером\n"\
                "Отчет о результатах автоматического тестирования"

servParams = f"\nПараметры подключения к серверу IEC 60870-5_104:\n\tIP-адрес: "\
                f"{DEFAULT_SERVER_IP}\n\tTCP-порт: {REAL_SERVER_PORT}"
                
servProtocolParams = """
Параметры протокола IEC 60870-5 104 для сервера:
    k = 12
    w = 8
    t1 = 15
    t2 = 10
    t3 = 20
"""
c = rkts.Client60870(port=REAL_SERVER_PORT,
                    address=DEFAULT_SERVER_IP,
                    bufferSize=1000)
p_k = str(c.paramAPCI.k)
p_w = str(c.paramAPCI.w)
p_t1 = str(c.paramAPCI.t1)
p_t2 = str(c.paramAPCI.t2)
p_t3 = str(c.paramAPCI.t3)
clientProtocolParams = f"\nПараметры протокола IEC 60870-5 104 для клиента:\n\t"\
                        f"k = {p_k}\n\tw = {p_w}\n\tt1 = {p_t1}\n\tt2 = {p_t2}\n\tt3 = {p_t3}\n"
W_OFF = "\nОТКЛЮЧЕНА функция автоматической отправки клиентом подтверждения " \
        "(APDU формата S) после получения им от сервера не более W блоков данных I-формата. \n"

header_log = (nameOfReport.center(115) + "\nВремя создания отчёта: " + time.strftime("%H:%M:%S")
            + servParams + servProtocolParams + clientProtocolParams + W_OFF)


def test_transmission(ip, K_parameter, write_log, csv):
    """В функции создаётся виртуальный клиент, на сервере запускается генерация \
    спорадики, выполняются тесты из раздела № 5.3.2.90 технической спецификации \
    IEC 60870-5-604. Результаты выполнения тестов и хронология событий, относящихся \
    к процедуре передачи данных между клиентом и сервером, записываются в лог-файл
    """

    if write_log:
        log(FILENAME, header_log)

    client = rkts.Client60870(port=REAL_SERVER_PORT,
                              address=ip,
                              bufferSize=1000)
    client.autoAckReachedW = False
    client.timerT2Work = False

    W_SERVER = 2*K_parameter/3

    spObj = rkts.IOSinglePoint()

    client.connect()

    # Проверка TCP-соединения
    assert client.isConnected == True, "Не удалось установить TCP-соединение между \
            клиентом и сервером"
    repConnection = "TCP-соединение между клиентом и сервером установлено.\n"
    print(repConnection)
    assert int(client.eventsCount) == 1,"Непредвиденное событие до старта передачи данных"

    # Telnet. Управление сменой значений LOC.Control.Alarm
    spGenerator(ip, switchings=14)
    print("Генерация спорадики запущена. Команда на старт передачи данных не отправлена клиентом")
    stagesHead = "\nЭтапы прохождения теста:\n"
    if write_log:
        log(FILENAME, stagesHead)

    client.sendStartDT()
    print("Клиентом отправлена команда на старт передачи данных")
    time.sleep(0.5)
    print(f"Количество принятых клиентом блоков данных "\
          f"I-формата после получения подтверждения от "\
          f"сервера: {client.unconfirmedRecvICount}")

# Проверка обмена блоками данных STARTDT_ACT -> <- STARTDT_CON
    startdt = u_frame_checker(client)
    assert "STARTDT_ACT" in startdt, "Блок данных U-формата НЕ содержит "\
            "функцию STARTDT_ACT"
    assert "STARTDT_CON" in startdt, "Блок данных U-формата НЕ содержит "\
            "подтверждение STARTDT_CON"

# Вывод сообщений об обмене U-фреймами STARTDT (Act) (Con)
    startdt_sent = f"Клиентом отправлен блок данных U-формата, "\
                    f"содержащий функцию {client.events()[1].data.type}\n"
    startdt_conf_rcvd = f"Клиентом получено подтверждение (блок данных U-формата "\
            f"с функцией {client.events()[2].data.type}\n"
    print(f"{exact_time(client.events()[1].timestamp)} {startdt_sent}")
    print(f"{exact_time(client.events()[2].timestamp)}  {startdt_conf_rcvd}")
    checkSTARTDT = startdt_sent + startdt_conf_rcvd
    if write_log:
        log(FILENAME, checkSTARTDT)
    unconfRecIFrames_0 = int(client.unconfirmedRecvICount)

# Проверка доставки блоков данных I-формата клиенту
    assert unconfRecIFrames_0 > 0,"Клиент не получил ни одного блока данных I-формата"

# Проверяем, что APDU блока данных соответствует I-формату
    assert client.events()[3].type in type_I_frame,"После получения подтверждения подтверждения от "\
            "сервера (STARTDT_Con) клиенту поступил блок данных не I-формата"

# Проверяем, что начальные значения передаваемого N(S) и принимаемого N(R) порядковых
# номеров установлены равными 0
    assert int(client.events()[3].data.recvCount) == 0,"Начальное значение передаваемого "\
            "порядкового номера блока данных не равно 0"

    assert int(client.events()[3].data.sentCount) == 0,"Начальное значение принимаемого "\
            "порядкового номера блока данных не равно 0"
            
    seq_numbers_first_I = "Значения передаваемого и принимаемого порядковых номеров "\
            "первого блока данных I-формата установлены равными 0\n"
    
    if write_log:
        log(FILENAME, seq_numbers_first_I)

    # Проверяем, что количество блоков данных I-формата соответствует значению K сервера
    assert int(client.unconfirmedRecvICount) == K_parameter,"Количество неподтверждённых блоков данных I-формата отлично от K"

    unconfRecIFrames_1 = int(client.unconfirmedRecvICount)
    log_check_K = f"Сервер отправил клиенту блоки данных I-формата в количестве, соответствующем значению K ({K_parameter})\n"

    if write_log:
        log(FILENAME,log_check_K)

#### Создаём список, содержащий передаваемые порядковые номера I-фреймов
    sendSeqNumbers = []
    for event in client.events():
        if event.type == rkts.EventType.I_FRAME_PROCESS_INFO_MON_DIR or event.type == rkts.EventType.END_OF_INIT:
            sendSeqNumbers.append(int(event.data.recvCount))
        else: continue

    # Проверяем инкрементацию N(S)
    assert sendSeqNumbers == list(range(K_parameter)),"Нарушена последовательность порядковых номеров передаваемых кадров"

    incrementOk = "Порядковый номер передачи каждого следующего блока данных I-формата увеличивается на 1\n"

    if write_log:
        log(FILENAME, incrementOk)

    # Отправляем серверу первый S-фрейм, который подтвердит K I-фреймов
    client.sendSFrame(unconfRecIFrames_1)       
    print(f"Отправили S-frame, подтверждающий {unconfRecIFrames_1} блоков данных I-формата")
    time.sleep(0.5)

    assert int(client.unconfirmedRecvICount)>unconfRecIFrames_1, "Сервер не совершал отправку \
        блоков данных I-формата после подтверждения"
    acknowledgement = f"Полученные клиентом от сервера блоки данных I-формата "\
                      f"были подтверждены APDU S-формата (S({K_parameter}))\n"
    if write_log:
        log(FILENAME, acknowledgement)

    client.sendSFrame(unconfRecIFrames_1)       # Отправили неподтверждающий S-фрейм
    time.sleep(0.5)
    unconfRecIFrames_2 = int(client.unconfirmedRecvICount)
    print(f"Отправили S-frame с порядковым номером {unconfRecIFrames_1} вместо подтверждающего "\
        f"порядкового номера {unconfRecIFrames_2}")
    time.sleep(0.5)

    # Проверка действия Сервера при отправке ему принимаемого порядкового номера N(R)<N(S)
    assert client.events()[-1].type == rkts.EventType.S_FRAME,"Непредвиденное получение клиентом \
        блококв данных I-формата. "
    
    sent_unconfirming_frame = f"Повторно отправленный клиентом APDU формата S({unconfRecIFrames_1}) "\
        f"(вместо S({unconfRecIFrames_2}) не привёл к подтверждению новых APDU сервера\n"

    if write_log:
        log(FILENAME, sent_unconfirming_frame)

    confirm_2_frames = int(unconfRecIFrames_1) + 2
    client.sendSFrame(confirm_2_frames)       # Посмотреть, сколько поступило I-фреймов
    num_of_events_1 = int(client.eventsCount)
    time.sleep(0.5)
    num_of_events_2 = int(client.eventsCount)

    assert (num_of_events_2 - num_of_events_1) == 2, "Ошибка количества поступивших неподтверждённых блоков данных!"
    assert client.events()[-2].type in type_I_frame, "Проверка подтверждения двух блоков данных I-формата не пройдена"
    assert client.events()[-1].type in type_I_frame, "Проверка подтверждения двух блоков данных I-формата не пройдена"

    confirm_two_frames = f"Отправленный клиентом контрольный формат S({confirm_2_frames}) подтвердил 2 APDU сервера.\n"\
        "Клиент получил 2 новых блока данных I-формата.\n"

    if write_log:
        log(FILENAME, confirm_two_frames)

    client.sendIO(spObj, rkts.CauseOfTransmission.COT_ACTIVATION, 1)

    print(f"Клиентом отправлен блок данных I-формата, содержащий функцию {spObj.type}")
    eventsWithSentIFrame = int(client.eventsCount)
    time.sleep(0.8)
    eventsAfterSentIFrame = int(client.eventsCount)

    assert eventsAfterSentIFrame > eventsWithSentIFrame,"Отсутствуют неподтверждённые блоки данных I-формата"

    dif = eventsWithSentIFrame - eventsAfterSentIFrame

    i = int(client.events()[dif].data.recvCount)

    for e in range(dif,0,1):
        assert client.events()[e].data.isSent == False, "Блок данных отправлен ошибочно!"
        assert client.events()[e].type in type_I_frame, "Клиентом получен APDU, не соответствующий формату I"
        assert client.events()[e].data.sentCount == 1,"Ошибка инкрементирования принимаемого порядкового номера сервера"
        assert int(client.events()[e].data.recvCount) == i, "Ошибка инкрементирования передаваемого порядкового номера сервера"
        i+=1

    client_sent_I_frame = "Отправленный клиентом APDU формата I подтвердил принятые от сервера APDU формата I.\n"\
        "После получения одного APDU от клиента, номер принятого кадра сервера увеличился на 1\n"

    if write_log:
        log(FILENAME, client_sent_I_frame)

    received_S = confirmation_of_W(client, eventsAfterSentIFrame)

    # print(f"Количество поступивших от сервера S-фреймов = {len(received_S)}")

    assert len(received_S) == 1,"Отправленные клиентом I-фреймы не подтверждены"

    cur_count_of_events = int(client.eventsCount)


    recv_S_frame = confirmation_of_W(client,cur_count_of_events, delay=0.7)

    # print(f"Количество поступивших от сервера S-фреймов = {len(recv_S_frame)}")

    assert len(recv_S_frame) != 0,"Отправленные во второй раз клиентом I-фреймы не подтверждены"
    assert len(recv_S_frame) < 2,"От сервера поступило 2 подтверждения вместо одного"

    check_param_W = f"На полученные от клиента APDU формата I в количестве, не превысившем {W_SERVER}, "\
        "сервер ответил подтверждающим APDU формата S\n"
    
    if write_log:
        log(FILENAME, check_param_W)

    time.sleep(0.5)

    client.sendStopDT()
    time.sleep(0.5)

    stopdt = u_frame_checker(client)

    assert "STOPDT_ACT" in stopdt,"Клиентом не отправлена команда прекращения передачи данных (STOPDT_Act)"
    assert "STOPDT_CON" in stopdt,"Клиентом не получено подтверждение прекращения передачи данных (STOPDT_Con)"

    STOPDT_complete = "Процедура прекращения передачи данных, инициированная клиентом, выполнена без ошибок"

    if write_log:
        log(FILENAME, STOPDT_complete)
        print("Отчёт сформирован в папке ", os.path.dirname(os.path.abspath(__file__)))

    client.disconnect()

    if csv:
        events_in_csv(client)
