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
det = 1




KServer = str(K_SERVER)
WServer = str(W_SERVER)
t1server = str (t1_SERVER)
t2server = str (t2_SERVER)
t3server = str (t3_SERVER)


type_I_frame = (rkts.EventType.I_FRAME_PROCESS_INFO_MON_DIR,
                rkts.EventType.END_OF_INIT,
                rkts.EventType.I_FRAME_PROCESS_INFO_CONTR_DIR)


def test_M_SP_NA_1(IP,PORT,t1_SERVER,det):
### Настройки
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    FILENAME = "identification_test.txt"

    client = rkts.Client60870(port=PORT,
                              address=IP,
                              bufferSize=1000)

    client.autoAckReachedW = True         
    client.timerT2Work = False              
    client.timerT1Work = False
    client.autoAckTestFrame = False
    client.timerT3Work = False               
    

    SPONT = rkts.CauseOfTransmission.COT_SPONTANEOUS
    INROGEN = rkts.CauseOfTransmission.COT_INTERROGATED_BY_STATION
    REQUEST = rkts.CauseOfTransmission.COT_REQUEST
    
    ACT = rkts.CauseOfTransmission.COT_ACTIVATION

    type = "M_SP_NA_1"
    vchel = 690
    qchel = 691
    adr = 1
    value = [1,0]
    q = [-64,472,64,0,216,192]
    blocked = [1,0,0,0,1,0]
    substituted = [0,1,0,0,1,0]
    nonTopical = [0,0,1,0,0,0]
    invalid = [0,0,0,1,0,0]


#### Установка соединения по Telnet
    tnConParams = {"ip" : IP, "port" : "23","login" : "root","pass" : "fhbc'rcg","timeout":60}
    
    tn_obj = tnc(tnConParams)
    tn_obj.connect()



    ioa = 1013
    client.connect()

    client.sendStartDT()

#### Проверка StartDT_con
    i = 0
    cmderr= "warehouse_set -n LOC.quality_test.AI-"+str(vchel)+" -v 0 -q 192"
    qcmderr = "warehouse_set -n LOC.quality_test.AI-"+str(qchel)+" -v 192 -q 192"
    testfr = u_frame_checker(client)


    while (str(testfr[-1].data.type) != "STARTDT_CON") and (i <= t1_SERVER + 1):
        testfr = u_frame_checker(client)
        time.sleep(0.1)
 
        i += 0.1

    if i >= t1_SERVER + 1:
        testcon = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.4.10: !Ошибка:\tПосле отправки команды STARTDT_ACT клиентом не получен STARTDT_CON"
        log(FILENAME,testcon)
        assert str(testfr[-1].data.type) == "STARTDT_CON", "Не получен STARTDT_CON"

#### STEP 1. Подстановка значений, отправка команд interrogation, и readcommand
    print("Проверка значения")
    
    for t in range(0,len(value)):
        a = str(value[t])
#### Подстановка значений
        cmd = "warehouse_set -n LOC.quality_test.AI-"+str(vchel)+" -v"+ a +" -q 192"
        tn_obj.run_command(cmd)
#### Ожидаем получения I кадров с причиной spont

        recv_I_frame_spont = I_frame_checker_Spont(client,ioa,type,SPONT,adr)
    
        d = 0

        while ((len(recv_I_frame_spont) == 0) or (recv_I_frame_spont[-1].value != value[t])) and (d <= det):
            recv_I_frame_spont = I_frame_checker_Spont(client,ioa,type,SPONT,adr)
            time.sleep(0.1)
            d += 0.1

        if d > det:
            testcon = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.4.10: !Ошибка:     Не получен I кадр с причиной <3> spont (спорадически) с значением "+ a
            log(FILENAME,testcon)

            tn_obj.run_command(cmderr)
            time.sleep(0.5)
            assert d <= det, " Не получен I кадр с причиной spont (спорадически) с значением "+ a 

### Отправка команды readcommand и ожидание нужного I кадра    
        client.sendReadCommand(ioa,REQUEST,adr)
        recv_I_frame_request = I_frame_checker_requst(client,ioa,type,REQUEST,adr)      # ???
        readc = 0

        while ((len(recv_I_frame_request) == 0) or (recv_I_frame_request[-1].value != value[t])) and (readc <= det):
            recv_I_frame_request = I_frame_checker_requst(client,ioa,type,REQUEST,adr)
            time.sleep(0.1)
            readc += 0.1
        
        if readc > det:
            testcon = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.4.10: !Ошибка:     Не получен I кадр с причиной <5> request (запрос или запрашиваемые данные) с значением "+ a 
            log(FILENAME,testcon)

            tn_obj.run_command(cmderr)
            time.sleep(0.5)
            assert readc <= 1, "Не получен I кадр с причиной <5> request (запрос или запрашиваемые данные) с значением "+ a 
        
### Отправка команды GI и ожидание нужного I кадра
        inrogcon = 0 
        client.sendInterrogationCommand(0,rkts.QOI.STATION,ACT, adr)

        recv_I_frame_inrogen = I_frame_checker_inrogen(client,ioa,type,INROGEN,adr)

        while((len(recv_I_frame_inrogen) == 0) or (recv_I_frame_inrogen[-1].value != value[t])) and (inrogcon <= det):
            recv_I_frame_inrogen = I_frame_checker_inrogen(client,ioa,type,INROGEN,adr)
            time.sleep (0.1)
            inrogcon += 0.1

        if inrogcon > det:
            testcon = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.4.10: !Ошибка:     Не получен I кадр с причиной <20> inrogen (ответ на опрос станции) с значением "+ a
            log(FILENAME,testcon)

            tn_obj.run_command(cmderr)
            time.sleep(0.5)
            assert inrogcon <= det, "Не получен I кадр с причиной <20> inrogen (ответ на опрос станции) с значением "+ a
        
        cmdI = I_frame_checker_cmd(client)
        l = 0
#### Ожидаем получения actTerm      
        while ((len(cmdI) == 0) or (cmdI[-1].data.cmd.cot != rkts.CauseOfTransmission.COT_ACTIVATION_TERMINATION))  and (l <= det):
            cmdI = I_frame_checker_cmd(client)
            time.sleep(0.1)
            l += 0.1

        if l > det:
            testcon = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.4.10: !Ошибка:      Не получен I кадр с причиной actTerm после выполнения команды genteral inerrogation (значение)"
            log(FILENAME,testcon)

            tn_obj.run_command(cmderr)
            time.sleep(0.5)
            assert det <= 1, "Не получен I кадр с причиной actTerm после выполнения команды genteral inerrogation (значение)"

#### Проверка неизменности качества при установке значения

        if (recv_I_frame_spont[-1].q.value != 0)  or   (recv_I_frame_request[-1].q.value != 0) or (recv_I_frame_inrogen[-1].q.value != 0):
            errq= """
"""+time.strftime("%Y%m%d_%H.%M")+""" Autotest 5.3.4.10: !Ошибка:     При смене значений изменилось качество (при значении """+ a +""")\n
Значение качества при spont = """ + str(recv_I_frame_spont[-1].q.value) +""" (Ожидался 0 (192))
Значение качества при request = """ + str(recv_I_frame_request[-1].q.value) +""" (Ожидался 0 (192)) 
Значение качества при inrogen = """ + str(recv_I_frame_inrogen[-1].q.value) +""" (Ожидался 0 (192))
"""  
            log(FILENAME,errq)
            tn_obj.run_command(qcmderr)
            tn_obj.run_command(cmderr)            
            time.sleep(0.5)
            assert (recv_I_frame_spont[-1].q.value == 0)  and   (recv_I_frame_request[-1].q.value == 0) and (recv_I_frame_inrogen[-1].q.value == 0)

### STEP 2. Проверка качества
    print("Проверка качества")
    
    for qt in range(0,len(q),1):
        qc = str(q[qt])
#### Подстановка значений
        qcmd = "warehouse_set -n LOC.quality_test.AI-"+str(qchel)+" -v"+ qc +" -q 192"
        tn_obj.run_command(qcmd)

    #### Ожидаем получения I кадров с причиной spont
        recv_I_frame_spont = I_frame_checker_Spont(client,ioa,type,SPONT,adr)
        q_I1 = recv_I_frame_spont[-1].q
        dq = 0
        while ((q_I1.blocked != blocked[qt]) or q_I1.substituted != substituted[qt] or q_I1.nonTopical != nonTopical[qt] or q_I1.invalid != invalid[qt] ) and (dq <= det):
            recv_I_frame_spont = I_frame_checker_Spont(client,ioa,type,SPONT,adr)
            q_I1 = recv_I_frame_spont[-1].q
            time.sleep(0.1)
            dq += 0.1
       
        if dq > det:
            bitq1= """
"""+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.4.10: !Ошибка:     Не получен I кадр с причиной <3> spont (спорадически) с качеством """+ qc + """
BL = """ + str(q_I1.blocked) +""" (Ожидался """ + str(blocked[qt]) +""" )
SB = """ + str(q_I1.substituted) +""" (Ожидался """ + str(substituted[qt]) +""" ) 
NT = """ + str(q_I1.nonTopical) +""" (Ожидался """ + str(nonTopical[qt]) +""" )
IV = """ + str(q_I1.invalid) +""" (Ожидался """ + str(invalid[qt]) +""" )
"""
            log(FILENAME,bitq1)

            tn_obj.run_command(qcmderr)
            time.sleep(0.5)
            assert dq <= det, " Не получен I кадр с причиной <3> spont (спорадически) с качеством "+ qc     
    
### Отправка команды readcommand и ожидание нужного I кадра    
        client.sendReadCommand(ioa,REQUEST,adr)
        
        recv_I_frame_request = I_frame_checker_requst(client,ioa,type,INROGEN,adr)
        q_I2 = recv_I_frame_request[-1].q
        qr = 0


        while ((q_I2.blocked != blocked[qt]) or q_I2.substituted != substituted[qt] or q_I2.nonTopical != nonTopical[qt] or q_I2.invalid != invalid[qt] ) and (qr <= det):
            recv_I_frame_request = I_frame_checker_requst(client,ioa,type,SPONT,adr)
            q_I2 = recv_I_frame_request[-1].q
            time.sleep(0.1)
            qr += 0.1
        if qr > det:
            bitq2= """
"""+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.4.10: !Ошибка:     Не получен I кадр с причиной <5> request (запрос или запрашиваемые данные) с качеством """+ qc + """
BL = """ + str(q_I2.blocked) +""" (Ожидался """ + str(blocked[qt]) +""" )
SB = """ + str(q_I2.substituted) +""" (Ожидался """ + str(substituted[qt]) +""" ) 
NT = """ + str(q_I2.nonTopical) +""" (Ожидался """ + str(nonTopical[qt]) +""" )
IV = """ + str(q_I2.invalid) +""" (Ожидался """ + str(invalid[qt]) +""" )
"""
            log(FILENAME,bitq2)

            tn_obj.run_command(qcmderr)
            time.sleep(0.5)
            assert qr <= det, " Не получен I кадр с причиной <5> request (запрос или запрашиваемые данные) с качеством "+ qc   

### Отправка команды GI и ожидание нужного I кадра

        client.sendInterrogationCommand(0,rkts.QOI.STATION,ACT, adr)
        recv_I_frame_inrogen = I_frame_checker_inrogen(client,ioa,type,INROGEN,adr)
        q_I3 = recv_I_frame_inrogen[-1].q
        qi = 0

        while ((q_I3.blocked != blocked[qt]) or q_I3.substituted != substituted[qt] or q_I3.nonTopical != nonTopical[qt] or q_I3.invalid != invalid[qt] ) and (qi <= det):
            recv_I_frame_inrogen = I_frame_checker_inrogen(client,ioa,type,SPONT,adr)
            q_I3 = recv_I_frame_inrogen[-1].q
            time.sleep(0.1)
            qi += 0.1
        if qi > det:
            bitq3= """
"""+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.4.10: !Ошибка:      Не получен I кадр с причиной <20> inrogen (ответ на опрос станции) с качеством """+ qc + """
BL = """ + str(q_I3.blocked) +""" (Ожидался """ + str(blocked[qt]) +""" )
SB = """ + str(q_I3.substituted) +""" (Ожидался """ + str(substituted[qt]) +""" ) 
NT = """ + str(q_I3.nonTopical) +""" (Ожидался """ + str(nonTopical[qt]) +""" )
IV = """ + str(q_I3.invalid) +""" (Ожидался """ + str(invalid[qt]) +""" )
"""
            log(FILENAME,bitq3)

            tn_obj.run_command(qcmderr)
            time.sleep(0.5)
            assert qr <= det, "  Не получен I кадр с причиной <20> inrogen (ответ на опрос станции) с качеством "+ qc   

#### Ожидаем получения actTerm        
        cmdIq = I_frame_checker_cmd(client)
        ql = 0
        while ((len(cmdI) == 0) or (cmdIq[-1].data.cmd.cot != rkts.CauseOfTransmission.COT_ACTIVATION_TERMINATION))  and (ql <= det):
            cmdI = I_frame_checker_cmd(client)
            time.sleep(0.1)
            ql += 0.1

        if ql > det:
            testcon = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.4.10: !Ошибка:      Не получен I кадр с причиной actTerm после выполнения команды genteral inerrogation (качество)"
            log(FILENAME,testcon)

            tn_obj.run_command(qcmderr)
            time.sleep(0.5)
            assert ql <= det, "Не получен I кадр с причиной actTerm после выполнения команды genteral inerrogation (качество)"
    
        if (recv_I_frame_spont[-1].value != 0)  or   (recv_I_frame_request[-1].value != 0) or (recv_I_frame_inrogen[-1].value != 0):
            errq= """
"""+time.strftime("%Y%m%d_%H.%M")+""" Autotest 5.3.4.10: !Ошибка:     При смене качества изменилось значение  (при качетсве """ + qc +""")\n
Значение  при spont = """ + str(recv_I_frame_spont[-1].value) +""" (Ожидался 0)
Значение  при request = """ + str(recv_I_frame_request[-1].value) +""" (Ожидался 0) 
Значение  при inrogen = """ + str(recv_I_frame_inrogen[-1].value) +""" (Ожидался 0)
"""  
            log(FILENAME,errq)
            tn_obj.run_command(qcmderr)
            tn_obj.run_command(cmderr)            
            time.sleep(0.5)   
            assert (recv_I_frame_spont[-1].value == 0)  and   (recv_I_frame_request[-1].value == 0) and (recv_I_frame_inrogen[-1].value == 0)

    losecont = "\n"+time.strftime("%Y%m%d_%H.%M")+" Autotest 5.3.4.10: Пройдено:     identification test M_SP_NA_1"
    log(FILENAME,losecont)

        

    


        


