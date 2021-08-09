import telnetlib


class TelnetEngine():

    TIMEOUT = 5

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

    def connect(self):
        self.telnet = telnetlib.Telnet(self.ip, self.port)
        return self

    def log_in(self, login, password):
        try:
            self.telnet.read_until(b"login: ", timeout=self.TIMEOUT)
            self.telnet.write(login.encode("utf-8") + b"\n")
            self.telnet.read_until(b"Password:", timeout=self.TIMEOUT)
            self.telnet.write(password.encode("utf-8") + b"\n")
            self.telnet.read_until(b'#', timeout=self.TIMEOUT)   
            self.connected = True
        except Exception:
            self.connected = False
    
    def is_connected(self):
        return self.connected

    def run_command(self, command):
        self.telnet.write(command.encode("utf-8") + b"\n")
        self.telnet.read_until(b'#', self.TIMEOUT)

    def disconnect(self):
        self.telnet.close()