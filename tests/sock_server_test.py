import os
import sys
sys.path.insert(0, os.path.abspath('lib'))
import candy_board_amt
from emulator_serialport import SerialPortEmurator
import pytest

@pytest.fixture(scope='function')
def setup_sock_server(request):
    serialport = SerialPortEmurator()
    return candy_board_amt.SockServer('devel', \
        {'apn': 'apn', 'user': 'apn_user', 'password': 'apn_password'}, \
        '/var/run/candy-board-service.sock', \
        serialport)

def test_perform_nok(setup_sock_server):
    ret = setup_sock_server.perform({'category':'no-such-category', 'action':'no-such-action'})
    assert ret == '{"status": "ERROR", "result": "Unknown Command"}'

def test_perform_nok2(setup_sock_server):
    ret = setup_sock_server.perform({})
    assert ret == '{"status": "ERROR", "result": "Invalid Args"}'

def test_apn_ls(setup_sock_server):
    ret = setup_sock_server.perform({'category':'apn', 'action':'ls'})
    assert ret == '{"status": "OK", "result": {"apns": [{"apn": "access_point_name", "user": "user_id", "apn_id": "1"}]}}'

def test_apn_set(setup_sock_server):
    ret = setup_sock_server.perform({'category':'apn', 'action':'set', 'name':'apn', 'user_id':'user', 'password':'password'})
    assert ret == '{"status": "OK", "result": ""}'

def test_apn_del(setup_sock_server):
    ret = setup_sock_server.perform({'category':'apn', 'action':'del', 'apn_id':'1'})
    assert ret == '{"status": "OK", "result": ""}'

def test_apn_set_nok(setup_sock_server):
    ret = setup_sock_server.perform({'category':'apn', 'action':'set'})
    assert ret == '{"status": "ERROR", "result": "Invalid Args"}'

def test_network_show(setup_sock_server):
    ret = setup_sock_server.perform({'category':'network', 'action':'show'})
    assert ret == '{"status": "OK", "result": {"rssi": "-105", "network": "ONLINE", "rssiDesc": ""}}'

def test_sim_show(setup_sock_server):
    ret = setup_sock_server.perform({'category':'sim', 'action':'show'})
    assert ret == '{"status": "OK", "result": {"msisdn": "09099999999", "state": "SIM_STATE_READY", "imsi": "440111111111111"}}'

def test_modem_show(setup_sock_server):
    ret = setup_sock_server.perform({'category':'modem', 'action':'show'})
    assert ret == '{"status": "OK", "result": {"imei": "999999999999999", "model": "MOD", "revision": "REV", "manufacturer": "MAN"}}'

def test_modem_enable_ecm(setup_sock_server):
    ret = setup_sock_server.perform({'category':'modem', 'action':'enable_ecm'})
    assert ret == '{"status": "OK", "result": ""}'

def test_modem_enable_ecm(setup_sock_server):
    ret = setup_sock_server.perform({'category':'modem', 'action':'enable_acm'})
    assert ret == '{"status": "OK", "result": ""}'

def test_service_version(setup_sock_server):
    ret = setup_sock_server.perform({'category':'service', 'action':'version'})
    assert ret == '{"status": "OK", "result": {"version": "devel"}}'
