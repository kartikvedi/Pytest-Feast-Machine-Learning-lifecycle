import re
import uuid
import logging
import socket
from typing import Dict
from threading import Lock
from paramiko.channel import ChannelFile
from ipaddress import IPv4Address, AddressValueError
from paramiko import SSHClient, MissingHostKeyPolicy


_log = logging.getLogger(__name__)


class UserMachine:
    def __init__(self, ip_address: str = "127.0.0.1", port: int = 22, user: str = "root", password: str = ""):
        self.__ip_address = self.__get_ip_address_from_host(ip_address)
        self.__port = port
        self.__user = user
        self.__password = password

    @staticmethod
    def __get_ip_address_from_host(host: str):
        try:
            return IPv4Address(host)
        except AddressValueError:
            try:
                ip = socket.gethostbyname(host)
                return IPv4Address(ip)
            except Exception:
                raise Exception("Couldn't retrieve IPv4 from provided host")

    def connect_to_ssh_client(self, client: SSHClient):
        client.connect(hostname=self.__ip_address.exploded, port=self.__port, username=self.__user,
                       password=self.__password)

    @property
    def ip(self):
        return self.__ip_address.exploded

    def __eq__(self, __o: object):
        if isinstance(__o, self.__class__):
            return self.__ip_address == __o.__ip_address and self.__port == __o.__port and self.__user == __o.__user
        return False

    def __hash__(self):
        return hash((self.__ip_address, self.__port, self.__user))

    def __str__(self):
        return f"UserMachine [IP={self.__ip_address}, port={self.__port}, user={self.__user}]"


class SingletonMeta(type):
    _instances = {}
    _lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class CLIObject(metaclass=SingletonMeta):
    __ssh_client_sessions: Dict[UserMachine, SSHClient] = {}
    __lock = Lock()

    def __del__(self):
        for _, client in self.__ssh_client_sessions.items():
            if client is not None:
                client.close()

    def __get_ssh_client_or_create(self, user_machine: UserMachine):
        with self.__lock:
            if user_machine in self.__ssh_client_sessions:
                return self.__ssh_client_sessions[user_machine]
            else:
                client = SSHClient()
                client.set_missing_host_key_policy(MissingHostKeyPolicy())
                user_machine.connect_to_ssh_client(client)
                self.__ssh_client_sessions[user_machine] = client
                return client

    def __get_ssh_client_from_obj_or_raise_exception(self, user_machine: UserMachine):
        if user_machine in self.__ssh_client_sessions:
            return self.__ssh_client_sessions[user_machine]
        else:
            raise Exception(f"Such {user_machine} doesn't exist in CLIObject")

    def __get_ssh_client_from_args_or_raise_exception(self, ip: str, port: int, user: str):
        user_machine = UserMachine(ip, port, user)
        return self.__get_ssh_client_from_obj_or_raise_exception(user_machine)

    @staticmethod
    def __exec_cmd(client: SSHClient, cmd: str):
        return client.exec_command(cmd)

    @staticmethod
    def __exec_cmd_with_output(client: SSHClient, cmd: str, match_string: str = None):
        res = False
        output = ''
        id_cmd = uuid.uuid4()
        _log.info(f"-------------> start  [ID: {id_cmd}] <-------------")
        _log.info(f"Current command is printed below:")
        _log.info(cmd)
        _, stdout, stderr = client.exec_command(cmd)

        def line_buffered(f: ChannelFile):
            line_buf = ""
            while not f.channel.exit_status_ready():
                line_buf += f.read(1).decode('utf-8')
                if line_buf.endswith('\n'):
                    yield line_buf
                    line_buf = ''
            if line_buf != '':
                yield line_buf

        for i, l in enumerate(line_buffered(stdout)):
            if i == 0 and l.strip() != "":
                _log.info(f"============-> stdout [ID: {id_cmd}] <-============")
            if match_string is not None and re.search(match_string, l) is not None:
                res = True
            output += l
            _log.info(l.strip())

        for i, l in enumerate(stderr.readlines()):
            if i == 0 and l.strip() != "":
                _log.info(f"============-> stderr [ID: {id_cmd}] <-============")
            _log.info(l.strip())
        _log.info(f"############=>   end  [ID: {id_cmd}] <=############")

        return res, output

    def init_connection_from_obj(self, user_machine: UserMachine):
        self.__get_ssh_client_or_create(user_machine)

    def init_connection_from_args(self, ip: str = "127.0.0.1", port: int = 22, user: str = "root", password: str = ""):
        self.__get_ssh_client_or_create(UserMachine(ip_address=ip, port=port, user=user, password=password))

    def exec_cmd_from_obj(self, user_machine: UserMachine, cmd: str):
        client = self.__get_ssh_client_or_create(user_machine)
        return self.__exec_cmd(client, cmd)

    def exec_cmd_with_output_from_obj(self, user_machine: UserMachine, cmd: str, match_string: str = None):
        """
        Execute command on remote host and match output line by line
        :param user_machine: UserMachine, which describes the host and user credentials
        :param cmd: str, bash command to execute
        :param match_string: String match to
        :return: tuple: bool True - string matched, False - no matched string found
                 string: stdout output of command
        """
        client = self.__get_ssh_client_or_create(user_machine)
        return self.__exec_cmd_with_output(client, cmd, match_string)

    def exec_cmd_from_args(self, ip: str = "127.0.0.1", port: int = 22, user: str = "root", password: str = None,
                           cmd: str = "id"):
        if password is not None:
            client = self.__get_ssh_client_or_create(UserMachine(ip_address=ip, port=port, user=user,
                                                                 password=password))
        else:
            client = self.__get_ssh_client_from_args_or_raise_exception(ip, port, user)
        return self.__exec_cmd(client, cmd)

    def exec_cmd_with_output_from_args(self, ip: str = "127.0.0.1", port: int = 22, user: str = "root",
                                       password: str = None, cmd: str = "id", match_string: str = None):
        """
        Execute command on remote host and match output line by line
        :param ip: str, IPv4 address of machine
        :param port: int, number of port, where SSH server is launched
        :param user: str, username which is present on this machine
        :param password: str, password for provided username
        :param cmd: str, bash command to execute
        :param match_string: String match to
        :return: tuple: bool True - string matched, False - no matched string found
                 string: stdout output of command
        """
        if password is not None:
            client = self.__get_ssh_client_or_create(UserMachine(ip_address=ip, port=port, user=user,
                                                                 password=password))
        else:
            client = self.__get_ssh_client_from_args_or_raise_exception(ip, port, user)
        return self.__exec_cmd_with_output(client, cmd, match_string)
