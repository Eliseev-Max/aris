# -*- coding: utf-8 -*-

import rkts
#from flaky import flaky
import os
import time
import datetime
import pytest
from arisconnector import ArisConnector, ArisTelnetConnector as tnc
from Tools.tools import *


# Включение/отключение логирования
LOGGING = False              # Консольный параметр
# Параметры сервера
REAL_SERVER_PORT = 2404
REAL_SERVER_ADDR = "10.1.32.253"
K_SERVER = 12               # Консольный параметр
W_SERVER = 8                # Консольный параметр

type_I_frame = (rkts.EventType.I_FRAME_PROCESS_INFO_MON_DIR,
                rkts.EventType.END_OF_INIT,
                rkts.EventType.I_FRAME_PROCESS_INFO_CONTR_DIR)

#Делаем каталог с исполняемым файлом текущим
os.chdir(os.path.dirname(os.path.abspath(__file__)))

FILENAME = f"{time.strftime('%Y%m%d_%H.%M')}_TransmissionProc_log.txt"
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
client_k = str(c.paramAPCI.k)
client_w = str(c.paramAPCI.w)
client_t1 = str(c.paramAPCI.t1)
client_t2 = str(c.paramAPCI.t2)
client_t3 = str(c.paramAPCI.t3)
clientProtocolParams = f"\nПараметры протокола IEC 60870-5 104 для клиента:\n\t"\
                        f"k = {client_k}\n\tw = {client_w}\n\tt1 = {client_t1}\n\t"\
                        f"t2 = {client_t2}\n\tt3 = {client_t3}\n"
W_OFF = "\nОТКЛЮЧЕНА функция автоматической отправки клиентом подтверждения " \
        "(APDU формата S) после получения им от сервера не более W блоков данных I-формата. \n"
header_log = (nameOfReport.center(115) + "\nВремя создания отчёта: " + time.strftime("%H:%M:%S")
            + servParams + servProtocolParams + clientProtocolParams + W_OFF)

if LOGGING:
    log(FILENAME, header_log)

# Создаём клиента IEC60870-5-104
client = rkts.Client60870(port=REAL_SERVER_PORT,
                          address=REAL_SERVER_ADDR,
                          bufferSize=1000)
client.autoAckReachedW = False
client.timerT2Work = False
spObj = rkts.IOSinglePoint()

client.connect()
time.sleep(0.4)
connection_status = client.isConnected


# Проверка TCP-соединения
def test_client_connected():
    assert connection_status,"Не удалось установить TCP-соединение между "\
                                        "клиентом и сервером"

repConnection = "TCP-соединение между клиентом и сервером установлено.\n"
print(repConnection)

count_of_events = int(client.eventsCount)


@pytest.mark.skip
def test_no_events_before_STARTDT():
    assert count_of_events == 1,"Непредвиденное событие до старта передачи данных"


# Telnet. Управление сменой значений LOC.Control.Alarm
spGenerator(REAL_SERVER_ADDR, switchings=14)
print("Генерация спорадики запущена. Команда на старт передачи данных "\
        "не отправлена клиентом")
stagesHead = "\nЭтапы прохождения теста:\n"

if LOGGING:
    log(FILENAME, stagesHead)

client.sendStartDT()
print("Клиентом отправлена команда на старт передачи данных")
time.sleep(0.5)
print(f"Количество принятых клиентом блоков данных "\
        f"I-формата после получения подтверждения от "\
            f"сервера: {client.unconfirmedRecvICount}")

# Проверка обмена блоками данных STARTDT_ACT -> <- STARTDT_CON
startdt = u_frame_checker(client)


def test_STARTDT_Act_confirmed_by_STARTDT_Con():
    assert "STARTDT_ACT" in startdt
    assert "STARTDT_CON" in startdt,"Процедура обмена \
        блоками данных U-формата (STARTDT_Act <--> STARTDT_Con) нарушена"

# Вывод сообщений об обмене U-фреймами STARTDT (Act) (Con)
startdt_log = "На кадр U-формата с управляющей функцией STARTDT_ACT получен ответ STARTDT_CON"

if LOGGING:
    log(FILENAME, startdt_log)

unconfRecIFrames_0 = int(client.unconfirmedRecvICount)

# Проверка доставки блоков данных I-формата клиенту

# if unconfRecIFrames_0 == 0:
#     no_I_frames = "\nОШИБКА!\nКлиентом не было получено ни одного "\
#         "блока данных I-формата"
#     if LOGGING:
#         log(FILENAME, no_I_frames)
#     raise Exception("Не получено ни одного I-фрейма")


first_N_sent = int(client.events()[3].data.recvCount)
first_N_recvd = int(client.events()[3].data.sentCount)
    
    
def test_initial_seq_numbers():
    assert first_N_sent == 0, "Начальное значение полученного порядкового "\
        "номера блока данных не установлено в 0" 
    assert first_N_recvd == 0,"Начальное значение передаваемого "\
        " порядкового номера блока данных не установлено в 0"

seq_numbers_first_I = "\nЗначения передаваемого и принимаемого порядковых номеров "\
                      "первого блока данных I-формата установлены равными 0"

if LOGGING:
    log(FILENAME, seq_numbers_first_I)

unconf_recv_I_frames_1 = int(client.unconfirmedRecvICount)


# Проверяем, что количество блоков данных I-формата соответствует значению K сервера
def test_received_K_I_frames():
    assert unconf_recv_I_frames_1 == K_SERVER,"Количество неподтверждённых блоков данных "\
                                        "I-формата не соответствует K"

log_check_K = f"\nСервер отправил клиенту блоки данных I-формата в количестве, соответствующем "\
                f"значению K ({K_SERVER})\n"

if LOGGING:
    log(FILENAME,log_check_K)

# Создаём список, содержащий передаваемые порядковые номера I-фреймов
sent_seq_numbers = []
recv_seq_numbers = []

for event in client.events():
    if event.type in type_I_frame:
        sent_seq_numbers.append(int(event.data.recvCount))
        recv_seq_numbers.append(int(event.data.sentCount))
    else: continue

recv_seq_nun_as_string = set(recv_seq_numbers)

# Проверяем инкрементацию N(S)
def test_counting_of_I_frames():
    assert sent_seq_numbers == list(range(unconf_recv_I_frames_1)),"Нарушена последовательность порядковых \
        номеров передаваемых кадров"
    assert recv_seq_nun_as_string == set([0])

incrementOk = "\nПорядковый номер передачи каждого следующего блока данных I-формата увеличивается на 1\n"

if LOGGING:
    log(FILENAME, incrementOk)

# Отправляем серверу первый S-фрейм, который подтвердит K I-фреймов
client.sendSFrame(unconf_recv_I_frames_1) 
print(f"Отправили S-frame, подтверждающий {unconf_recv_I_frames_1} блоков данных I-формата")
time.sleep(0.6)
unconf_recv_I_frames_2 = int(client.unconfirmedRecvICount)


def test_confirmation_by_S_frame():
    assert unconf_recv_I_frames_2 > unconf_recv_I_frames_1,"Сервер не совершал отправку блоков "\
                                                         "данных I-формата после подтверждения"

# if unconf_recv_I_frames_2 == unconf_recv_I_frames_1:
#     no_confirmation = "\nОШИБКА!\nПосле отправки S-фрейма клиентом не было "\
#         "получено ни однго блока данных I-формата"
#     if LOGGING:
#         log(FILENAME, no_confirmation)
#     raise Exception("После подтверждения не получено ни одного I-фрейма")

acknowledgement = "Полученные клиентом от сервера блоки данных I-формата "\
                  "были подтверждены блоком данных S-формата"

if LOGGING:
    log(FILENAME, acknowledgement)

# Отправляем неподтверждающий S-фрейм
client.sendSFrame(unconf_recv_I_frames_1)
time.sleep(0.5)
unconf_recv_I_frames_3 = int(client.unconfirmedRecvICount)

print(f"Отправили S-frame с порядковым номером {unconf_recv_I_frames_1} вместо "\
      f"подтверждающего порядкового номера {unconf_recv_I_frames_3}")
time.sleep(0.5)

last_obj_type = client.events()[-1].type


# Проверка действия Сервера при отправке ему принимаемого порядкового номера N(R)<N(S)
def test_send_no_confirming_S_frame():
    assert last_obj_type == rkts.EventType.S_FRAME, "Сервер возобновил передачу блоков "\
        "данных I-формата без получения подтверждения"

no_confirm_S_frame = f"\nПосле отправки блока данных S-формата, возвращающего "\
    f"порядковый номер принятого кадра S({unconf_recv_I_frames_1}), "\
    "новых блоков данных I-формата не получено"

if LOGGING:
    log(FILENAME, no_confirm_S_frame)

confirm_2_frames = int(unconf_recv_I_frames_1) + 2
client.sendSFrame(confirm_2_frames)

num_of_events_1 = int(client.eventsCount)
time.sleep(0.5)
num_of_events_2 = int(client.eventsCount)

event_type_1 = client.events()[-2].type
event_type_2 = client.events()[-1].type
two_last_events = [event_type_1, event_type_2]


@pytest.mark.parametrize("frame", two_last_events)
def test_two_I_frames_has_received(frame):
    assert (num_of_events_2 - num_of_events_1) == 2, "Ошибка количества поступивших "\
        "неподтверждённых блоков данных!"
    assert frame in type_I_frame,"Проверка подтверждения двух блоков данных I-формата"\
        " не пройдена"

confirm_2_frames = f"\nПосле отправки блока данных S-формата, возвращающего порядковый "\
                    f"номер принятого кадра S({confirm_2_frames}), "\
                    f"клиентом получено 2 блока данных I-формата"

if LOGGING:
    log(FILENAME, confirm_2_frames)

# Отправляем один I-фрейм, подтверждающий полученные клиентом блоки данных I-формата
client.sendIO(spObj, rkts.CauseOfTransmission.COT_ACTIVATION, 1)
print(f"Клиентом отправлен блок данных I-формата, содержащий функцию {spObj.type}")

events_with_client_sent_I = int(client.eventsCount)

time.sleep(0.6)

events_after_client_sent_I = int(client.eventsCount)
dif = events_with_client_sent_I - events_after_client_sent_I
events_collector = []
for e in range(dif,0,1):
    events_collector.append(client.events()[e])


def test_client_received_frames_after_sending_I_frame():
    assert events_after_client_sent_I > events_with_client_sent_I,"Отсутствуют неподтверждённые "\
        "блоки данных I-формата"
    for event in events_collector:
        assert event.type in type_I_frame, "Полученный клиентом блок данных не является I-фреймом"


def test_I_frames_received_count_number_became_1():
    for event in events_collector:
        assert event.data.sentCount == 1,"Ошибка инкрементирования принимаемого "\
                                                    "порядкового номера сервера"

confirming_I_frame = f"\nКлиентом был отправлен блок данных I-формата, подтвердивший 2 APDU сервера, "\
                        f"после чего клиентом было получено {abs(dif)} APDU от сервера.\n"

if LOGGING:
    log(FILENAME, confirming_I_frame)

# Проверка отправки подтверждения после получения не более W блоков данных I-формата
received_S_once = confirmation_of_W(client, events_after_client_sent_I, W=W_SERVER)
try:
    s_value_1 = received_S_once[0].data.sVal

except IndexError:
    print(f"ОШИБКА!!!\t Сервер не отправил S-фрейм, подтверждающий {W_SERVER} I-фреймов клиента")
    raise Exception("Тест аварийно остановлен")

else:

    def test_server_has_confirmed_I_frames():
        assert len(received_S_once) != [], "Отправленные клиентом I-фреймы не подтверждены"
        assert len(received_S_once) == 1, "Клиент получил более одного S-фрейма"

    conf_after_W = f"\nКлиент отправил серверу {W_SERVER} блоков данных I-формата "\
                f"и получил от сервера подтверждающий блок данных S-формата "\
                    f"S({s_value_1})"

if LOGGING:
    log(FILENAME, conf_after_W)

cur_count_of_events = int(client.eventsCount)

received_S_twice = confirmation_of_W(client,cur_count_of_events,W = W_SERVER , delay=0.7)
print(f"Количество поступивших от сервера S-фреймов = {len(received_S_twice)}")
try:
    s_value_2 = received_S_twice[0].data.sVal

except IndexError as ind:
    print(f"ОШИБКА!!!\t {ind}")

else:

    def test_server_has_confirmed_again_I_frames():
        assert len(received_S_twice) != [], "Повторно отправленные клиентом I-фреймы не подтверждены"
        assert len(received_S_twice) == 1, "Клиент получил более одного S-фрейма"

    conf_after_W = f"\nКлиент отправил серверу {W_SERVER} блоков данных I-формата "\
                    f"и получил от сервера подтверждающий блок данных S-формата "\
                        f"S({s_value_2})"

if LOGGING:
    log(FILENAME, conf_after_W)

time.sleep(0.5)
client.sendStopDT()
time.sleep(0.5)

stopdt = u_frame_checker(client)


def test_STOPDT_Act_confirmed_by_STOPDT_Con():
    assert "STOPDT_ACT" in stopdt,"Клиентом не отправлена команда прекращения "\
        "передачи данных (STOPDT_Act)"
    assert "STOPDT_CON" in stopdt,"Клиентом не получено подтверждение прекращения "\
        "передачи данных (STOPDT_Con)"

stopdt_log = "\nНа кадр U-формата с управляющей функцией STOPDT_ACT получен ответ STOPDT_CON"

if LOGGING:
    log(FILENAME, stopdt_log)

client.disconnect()

# Сортировка событий по типам с указанием метки времени
# listOfEvents = sort_events(client)
# stringOfEvents = "".join(listOfEvents)
# eventLog = "\nЖурнал событий:\n" + stringOfEvents

# if LOGGING:
#     log(FILENAME, eventLog)

# events_in_csv(client)
print("Отчёт сформирован в папке ", os.path.dirname(os.path.abspath(__file__)))
