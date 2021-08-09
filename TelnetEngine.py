import telnetlib

class ArisTelnetConnector():
    """
    Реализует telnet соединение с контроллером ARIS.
    :param access_params: словарь строковых параметров вида:
    {
        "ip" : "ip-адрес",
        "port" : "TCP-порт",
        "Login" : "имя пользователя",
        "pass" : "Пароль",
        "timeout" : "Таймаут в сек"
    }
    все методы возвращают кортеж (data, error):
    для устойчивости робот-скриптов минимизировано падение 
    при обрывах соедиений и задержек в канале.

    """

    def __init__(self, access_params):
        self.tn=None
        self.connect_error = "Connection to {} lost".format(self.access_params["ip"])
        
    def connect(self):
        host=self.access_params['ip']
        port=int(self.access_params['port'])
        login = self.access_params['login']
        passw = self.access_params['pass']
        self.timeout=float(self.access_params['timeout'])
        try:
            self.tn = telnetlib.Telnet(host,port,self.timeout)
            self.tn.read_until(b"login: ")
            self.tn.write(login.encode("utf-8") + b"\n")
            self.tn.read_until(b"Password:")
            self.tn.write(passw.encode("utf-8") + b"\n")
            self.tn.read_until(b'#', self.timeout)   
            self.connected=True
        except Exception:
            self.connected=False
    
    def disconnect(self):
        if self.tn:
            try:
                self.tn.close()
                self.tn = None
            except: pass
            self.connected=False
            
    def is_connected(self):
        try:
            self.tn.sock.sendall(IAC + NOP)
            return True
        except:
            return False

    def run_command(self, cmd):
        """
        Выполняет произвольную команду по telnet.
        :param cmd: строка команды без окончания "\n"
        возвращает кортеж вида (result, error)
        возвращает None при отсутствии одного из ответов

        """
        if not self.connected:
            return None, "Not connected"
        time.sleep(0.01)

        try:
            self.tn.write(cmd.encode("utf-8") + b"\n")
            self.tn.read_until(b'\n', self.timeout)
            result = self.tn.read_until(b'#', self.timeout).decode("utf-8")

        except (EOFError, ConnectionError):
            answer = (None, self.connect_error)

        else:
            answer = (result.split('#')[0].strip(), None)

        return answer

    def run_reboot_command(self, emergency=False):
        """
        при emergency=False (по умолчанию) выполняет команду "fullreboot".
        при emergency=True выполняет команду "reboot_to_emergency".
        возвращает кортеж вида (result, error)
        возвращает None при отсутствии ошибок
        возвращает result = True при выполнении команды

        """
        if not self.connected:
            return False, "Not connected"
        time.sleep(0.01)

        try:
            if emergency:
                self.tn.write(b"reboot_to_emergency\n")
            else:
                self.tn.write(b"fullreboot\n")

            result = self.tn.read_until(b'----------- Reboot -----------', self.timeout)
            result = result.decode("utf-8").split('#')[0].strip()

            if "Reboot" in result:
                answer = (True, None)
            else:
                answer = (False, "Unexpected answer")

        except (EOFError, ConnectionError):
            answer = (False, self.connect_error)

        return answer

    def run_unsafe_emergency_command(self):
        """
        Выполняет команду "devw-reset -ee".
        возвращает кортеж вида (result, error)
        возвращает None при отсутствии ошибок
        возвращает result = True при выполнении команды

        """
        if not self.connected:
            return False, "Not connected"
        time.sleep(0.01)

        try:
            self.tn.write(b"devw-reset -ee\n")
            time.sleep(2)
        except (EOFError, ConnectionError):
            answer = (False, self.connect_error)

        else:

            try:
                self.tn.write(b"\n")
                res = self.tn.read_until(b'#', self.timeout)
                if "#" in res.decode("utf-8"):
                    answer = (False, "Not rebooted")
                else:
                    answer = (True, None)

            except (EOFError, ConnectionError):
                answer = (True, self.connect_error)

            return answer

    def telnet_connect_to_other_aris(self, ip):
        """
        Выполняет команду "telnet ip".
        возвращает кортеж вида (result, error)
        возвращает None при отсутствии одного из ответов
        возвращает result = True при выполнении команды
        """
        if not self.connected:
            return False, "Not connected"
        time.sleep(0.01)

        try:
            self.tn.write("telnet {}".format(ip).encode("utf-8") + b"\n")
            log = self.tn.read_until(b"login: ", timeout = 10)
        except (EOFError, ConnectionError):
            answer = (False, self.connect_error)

        else:
            if "login" not in log.decode("utf-8"):
                answer = (False, "Connection to {} failed".format(ip))
                self.tn.write(b"\x03")
                self.tn.read_until(b'#', self.timeout)

            else:
                try:
                    self.tn.write(self.access_params['login'].encode("utf-8") + b"\n")
                    self.tn.read_until(b"Password:")
                    self.tn.write(self.access_params['pass'].encode("utf-8") + b"\n")
                    self.tn.read_until(b'#', self.timeout)  
                except (EOFError, ConnectionError):
                    answer = (False, self.connect_error)

                else:
                    answer = (True, None)

            return answer
        