#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fcntl
import json
import os
import socket
import select
import struct
import sys
import termios
import threading
import time
import glob
import platform
import traceback

# SerialPort class was imported from John Wiseman's
# https://github.com/wiseman/arduino-serial/blob/master/arduinoserial.py

# Map from the numbers to the termios constants (which are pretty much
# the same numbers).

BPS_SYMS = {
    4800:     termios.B4800,
    9600:     termios.B9600,
    19200:    termios.B19200,
    38400:    termios.B38400,
    57600:    termios.B57600,
    115200:   termios.B115200
    }


# Indices into the termios tuple.

IFLAG = 0
OFLAG = 1
CFLAG = 2
LFLAG = 3
ISPEED = 4
OSPEED = 5
CC = 6


def bps_to_termios_sym(bps):
    return BPS_SYMS[bps]

# For local debugging:
# import candy_board_amt
# serial = candy_board_amt.SerialPort("/dev/ttyUSB1", 115200)
# server = candy_board_amt.SockServer("/var/run/candy-iot.sock", serial)
# server.debug = True
# server.apn_ls()


class SerialPort(object):

    def __init__(self, serialport, bps):
        """Takes the string name of the serial port
        (e.g. "/dev/tty.usbserial","COM1") and a baud rate (bps) and
        connects to that port at that speed and 8N1. Opens the port in
        fully raw mode so you can send binary data.
        """
        self.fd = os.open(serialport, os.O_RDWR | os.O_NOCTTY | os.O_NDELAY)
        attrs = termios.tcgetattr(self.fd)
        bps_sym = bps_to_termios_sym(bps)
        # Set I/O speed.
        attrs[ISPEED] = bps_sym
        attrs[OSPEED] = bps_sym

        # 8N1
        attrs[CFLAG] &= ~termios.PARENB
        attrs[CFLAG] &= ~termios.CSTOPB
        attrs[CFLAG] &= ~termios.CSIZE
        attrs[CFLAG] |= termios.CS8
        # No flow control
        attrs[CFLAG] &= ~termios.CRTSCTS

        # Turn on READ & ignore contrll lines.
        attrs[CFLAG] |= termios.CREAD | termios.CLOCAL
        # Turn off software flow control.
        attrs[IFLAG] &= ~(termios.IXON | termios.IXOFF | termios.IXANY)

        # Make raw.
        attrs[LFLAG] &= ~(termios.ICANON | termios.ECHO |
                          termios.ECHOE | termios.ISIG)
        attrs[OFLAG] &= ~termios.OPOST

        # It's complicated--See
        # http://unixwiz.net/techtips/termios-vmin-vtime.html
        attrs[CC][termios.VMIN] = 0
        attrs[CC][termios.VTIME] = 20
        termios.tcsetattr(self.fd, termios.TCSANOW, attrs)

        self.ping()

    def read_until(self, until):
        buf = ""
        done = False
        while not done:
            n = os.read(self.fd, 1)
            if n == '':
                # FIXME: Maybe worth blocking instead of busy-looping?
                time.sleep(0.01)
                continue
            buf = buf + n
            if n == until:
                done = True
        return buf

    def read_line(self):
        try:
            return self.read_until("\n").strip()
        except OSError:
            return None

    def write(self, str):
        os.write(self.fd, str)

    def write_byte(self, byte):
        os.write(self.fd, chr(byte))

    def close(self):
        try:
            os.close(self.fd)
        except OSError:
            pass

    def ping(self, loop=3):
        ret = None
        for i in (0, loop):
            self.write("AT\r")
            time.sleep(0.1)
            line = self.read_line()
            if line is None:
                time.sleep(0.1)
                continue
            else:
                ret = ''
                while line is not None:
                    ret = ret + line + '\r'
                    line = self.read_line()
                break
        return ret

    @staticmethod
    def resolve_modem_port(bps=115200):
        if platform.system() != 'Linux':
            return None

        def open_serial_port(p):
            for i in (0, 3):
                port = None
                try:
                    port = SerialPort(p, bps)
                    return port
                except:
                    if port:
                        try:
                            port.close()
                        except:
                            pass
                    port = None
                    time.sleep(0.1)
                    pass
            return None

        for t in ['/dev/ttyUSB*', '/dev/ttyACM*', '/dev/ttyAMA*']:
            for p in sorted(glob.glob(t)):
                port = open_serial_port(p)
                if port is None:
                    continue
                ret = port.ping()
                if ret is None:
                    port.close()
                    continue
                if "OK" in ret:
                    port.close()
                    return p
                port.close()

        return None


class SockServer(threading.Thread):
    def __init__(self, version, apn,
                 sock_path="/var/run/candy-board-service.sock", serial=None):
        super(SockServer, self).__init__()
        self.version = version
        self.sock_path = sock_path
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.serial = serial
        self.debug = False
        if apn:
            cmd = {
                'name': apn['apn'],
                'user_id': apn['user'],
                'password': apn['password']
            }
            self.apn_set(cmd)

    def recv(self, connection, size):
        ready, _, _ = select.select([connection], [], [], 5)
        if ready:
            return connection.recv(size)
        else:
            raise IOError("recv Timeout")

    def run(self):
        self.sock.bind(self.sock_path)
        self.sock.listen(128)
        header_packer = struct.Struct("I")
        print("Listening to the socket[%s]...." % self.sock_path)

        while True:
            try:
                connection, client_address = self.sock.accept()
                connection.setblocking(0)

                # request
                header = self.recv(connection, header_packer.size)
                size = header_packer.unpack(header)
                unpacker_body = struct.Struct("%is" % size)
                cmd_json = self.recv(connection, unpacker_body.size)
                cmd = json.loads(cmd_json)

                # response
                message = self.perform(cmd)
                if message:
                    size = len(message)
                else:
                    size = 0
                packed_header = header_packer.pack(size)
                connection.sendall(packed_header)
                if size > 0:
                    packer_body = struct.Struct("%is" % size)
                    packed_message = packer_body.pack(message)
                    connection.sendall(packed_message)

            except:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                traceback.print_exception(exc_type, exc_value, exc_traceback)

            finally:
                if 'connection' in locals():
                    connection.close()

    def perform(self, cmd):
        try:
            if cmd['category'][0] == '_':
                raise AttributeError()
            m = getattr(self.__class__,
                        "%s_%s" % (cmd['category'], cmd['action']))
            return m(self, cmd)
        except AttributeError:
            return self.error_message("Unknown Command")
        except KeyError:
            return self.error_message("Invalid Args")
        except OSError:
            return self.error_message("I/O Error")
        except:
            return self.error_message("Unexpected error: %s" %
                                      (''.join(traceback
                                       .format_exception(*sys.exc_info())[-2:])
                                       .strip().replace('\n', ': '))
                                      )

    def error_message(self, msg):
        return json.dumps({"status": "ERROR", "result": msg})

    def read_line(self):
        line = self.serial.read_line()
        if self.debug:
            print("[modem:IN] => [%s]" % line)
        return line

    def send_at(self, cmd):
        line = "%s\r" % cmd
        if self.debug:
            print("[modem:OUT] => [%s]" % line)
        self.serial.write(line)
        time.sleep(0.1)
        result = ""
        status = None
        while True:
            line = self.read_line()
            if line is None:
                break
            elif line == cmd:
                continue
            elif line == "OK" or line == "ERROR":
                status = line
            elif line is None:
                status = "UNKNOWN"
            elif line.strip() != "":
                result += line + "\n"
        if self.debug:
            print("cmd:[%s] => status:[%s], result:[%s]" %
                  (cmd, status, result))
        return (status, result.strip())

    def _apn_ls(self):
        status, result = self.send_at("AT+CGDCONT?")
        apn_list = []
        if status == "OK":
            id_name_list = map(lambda e: e[10:].split(",")[0] + "," +
                               e[10:].split(",")[2].translate(None, '"'),
                               result.split("\n"))
            status, result = self.send_at("AT$QCPDPP?")
            creds_list = []
            if status == "OK":
                creds_list = map(lambda e: e[2].translate(None, '"'),
                                 filter(lambda e: len(e) > 2,
                                        map(lambda e: e[9:].split(","),
                                            result.split("\n"))))
            for i in range(len(id_name_list)):
                id_name = id_name_list[i].split(",")
                apn = {
                    'apn_id': id_name[0],
                    'apn': id_name[1]
                }
                if i < len(creds_list):
                    apn['user'] = creds_list[i]
                apn_list.append(apn)
        message = {
            'status': status,
            'result': {
                'apns': apn_list
            }
        }
        return message

    def apn_ls(self, cmd):
        return json.dumps(self._apn_ls())

    def apn_set(self, cmd):
        (name, user_id, password) = (cmd['name'], cmd['user_id'],
                                     cmd['password'])
        apn_id = "1"
        if 'apn_id' in cmd:
            apn_id = cmd['apn_id']
        status, result = self.send_at(("AT+CGDCONT=%s,\"IPV4V6\",\"%s\"," +
                                      "\"0.0.0.0\",0,0") % (apn_id, name))
        if status == "OK":
            status, result = self.send_at(("AT$QCPDPP=%s,3,\"%s\",\"%s\"") %
                                          (apn_id, password, user_id))
        message = {
            'status': status,
            'result': result
        }
        return json.dumps(message)

    def _apn_del(self, apn_id):
        # removes QCPDPP as well
        status, result = self.send_at(("AT+CGDCONT=%s") % apn_id)
        message = {
            'status': status,
            'result': result
        }
        return message

    def apn_del(self, cmd):
        apn_id = "1"
        if 'apn_id' in cmd:
            apn_id = cmd['apn_id']
        return json.dumps(self._apn_del(apn_id))

    def network_show(self, cmd):
        status, result = self.send_at("AT+CSQ")
        rssi = ""
        network = "UNKNOWN"
        rssi_desc = ""
        if status == "OK":
            rssi_level = int(result[5:].split(",")[0])
            if rssi_level == 0:
                rssi = "-113"
                rssi_desc = "OR_LESS"
            elif rssi_level == 1:
                rssi = "-111"
            elif rssi_level <= 30:
                rssi = "%i" % (-109 + (rssi_level - 2) * 2)
            elif rssi_level == 31:
                rssi = "-51"
                rssi_desc = "OR_MORE"
            else:
                rssi_desc = "NO_SIGANL"
            status, result = self.send_at("AT+CPAS")
            if status == "OK":
                state_level = int(result[6:])
                if state_level == 4:
                    network = "ONLINE"
                else:
                    network = "OFFLINE"
        message = {
            'status': status,
            'result': {
                'rssi': rssi,
                'rssiDesc': rssi_desc,
                'network': network
            }
        }
        return json.dumps(message)

    def sim_show(self, cmd):
        state = "SIM_STATE_ABSENT"
        msisdn = ""
        imsi = ""
        status, result = self.send_at("AT+CIMI")
        if status == "OK":
            imsi = result
            state = "SIM_STATE_READY"
            status, result = self.send_at("AT+CNUM")
            msisdn = result[6:].split(",")[1].translate(None, '"')
        message = {
            'status': status,
            'result': {
                'msisdn': msisdn,
                'imsi': imsi,
                'state': state
            }
        }
        return json.dumps(message)

    def modem_show(self, cmd):
        status, result = self.send_at("ATI")
        man = "UNKNOWN"
        mod = "UNKNOWN"
        rev = "UNKNOWN"
        imei = "UNKNOWN"
        if status == "OK":
            info = result.split("\n")
            man = info[0][14:]
            mod = info[1][7:]
            rev = info[2][10:]
            imei = info[3][6:]
        message = {
            'status': status,
            'result': {
                'manufacturer': man,
                'model': mod,
                'revision': rev,
                'imei': imei,
            }
        }
        return json.dumps(message)

    def modem_enable_auto_connect(self, cmd):
        status, result = self.send_at("AT@AUTOCONN?")
        if status == "OK":
            if result == "@AUTOCONN:0":
                # modem will reboot
                status, result = self.send_at("AT@AUTOCONN=1")
            else:
                result = "Already Enabled"
        message = {
            'status': status,
            'result': result
        }
        return json.dumps(message)

    def modem_enable_ecm(self, cmd):
        # modem will reboot, @AUTOCONN=0
        status, result = self.send_at("AT@USBCHG=ECM")
        message = {
            'status': status,
            'result': result
        }
        return json.dumps(message)

    def _modem_enable_acm(self):
        # modem will reboot, @AUTOCONN=0
        status, result = self.send_at("AT@USBCHG=ACM")
        message = {
            'status': status,
            'result': result
        }
        return message

    def modem_enable_acm(self, cmd):
        return json.dumps(self._modem_enable_acm())

    def modem_reset(self, cmd):
        """
        - Remove all APN
        - Change USB mode to ACM
        """
        apn_ls_ret = self._apn_ls()
        status = apn_ls_ret['status']
        result = ''
        if apn_ls_ret['status'] == "OK":
            apns = apn_ls_ret['result']['apns']
            for apn in apns:
                self._apn_del(apn['apn_id'])
            modem_enable_acm_ret = self._modem_enable_acm()
            status = modem_enable_acm_ret['status']
        message = {
            'status': status,
            'result': result
        }
        return json.dumps(message)

    def service_version(self, cmd):
        message = {
            'status': 'OK',
            'result': {
                'version': self.version,
            }
        }
        return json.dumps(message)
