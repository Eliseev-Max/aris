#-*- coding: utf-8 -*-
import telnetlib
import time
#ip = input("Введите IP-адрес контроллера\n")
ip = '10.1.32.253'
tn = telnetlib.Telnet(ip)
print("Connected by Telnet")
to_username = tn.read_until(b'login:')
tn.write(b'root\n')
to_pwd = tn.read_until(b'Password')
tn.write(b"fhbc'rcg\n")
print("Аутентификация завершена")
tn.read_until(b'#')                 #Подключение по Telnet и авторизация выполнены

# Собираем команду по частям
source = 'LOC.Control.Alarm'
val_1 = '1'
val_0 = '0'
q = '192'   # Значение качества сигнала
n = 0

# cmdstring_1 = "warehouse_set -n {0} -v {1} -q {2} \n".format(source, val_1, q)
# cmdstring_0 = "warehouse_set -n {0} -v {1} -q {2} \n".format(source, val_0, q)
wh_view = ""
#set_1 = tn.write(b'warehouse_set -n ' + source + ' -v ' + val_1 + ' -q ' +q+ '\n')
cmd1 = bytearray(cmdstring_1,"ascii")
cmd2 = bytearray(cmdstring_0,"ascii")
cmd_view = bytearray()

# while n<3:
#     set_1 = tn.write(cmd1)
#     print(f"Установлено значение:  ->  {val_1} \n")
#     time.sleep(1)
#     set_0 = tn.write(cmd2)
#     print(f"Установлено значение:  ->  {val_0} \n")
#     # print("Установлено значение: "+ client +" -> " + val_0 + "\n")
#     time.sleep(1)
#     n+=1

allRes = tn.read_very_eager().decode('utf-8')
print(f"Вывожу результат: {allRes}")

tn.close()

