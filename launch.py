import os, sys, getopt
import asyncio
import contextlib
import serial_asyncio
import configparser

# default config
connect_type = 'rs232'
verbose_p = False # first level of verbosity
verbose_pp = False # second level of verbosity
device_addr = '/dev/ttyUSB0' # Com port-connected
timeout_for_verification = 5 # seconds
# EOF config

# tech config
config_filename = 'config.ini'
baud_rate = 9600 # for R232 it's arguably the best working option
conn_tout = 1
# Interaction codes with the board
code_for_granted              = b'\x01'
code_for_denied               = b'\x00'
code_for_ping                 = b't'
code_for_request              = b'r'
code_for_silent_request       = b's'
code_for_request_user         = b'u'
code_for_silent_request_user  = b'y'
# EOF tech config

#init vars
check_for_user = False
verbose = verbose_p or verbose_pp
verbose_p = verbose_p or verbose_pp
a_level = None
get_next_byte = False
users_list = None
# init objects
access_task = asyncio.Event()

def device_exists(path):
    """Test whether a path exists.  Returns False for broken symbolic links"""
    try:
        os.stat(path)
    except OSError:
        return False
    return True


class OutputProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        global verbose_p, verbose_pp
        self.transport = transport
        if verbose_pp:
            print('[ INFO ] port opened', transport)
        transport.serial.rts = False  # You can manipulate Serial object via transport
        if check_for_user:
            transport.write(code_for_request_user)  # Write serial data via transport
        else:
            transport.write(code_for_request)  # Write serial data via transport

    def data_received(self, data):
        global a_level, code_for_granted, code_for_denied, code_for_ping, get_next_byte, verbose_p, verbose_pp
        if verbose_pp:
            print('[ INFO ] data received', repr(data))
        if get_next_byte:
            a_level = data[:1]
            if verbose_p:
                print("[ INFO ] User id code received: \"{0}\"".format(int(data)))
            access_task.set()
        elif data == code_for_ping:
            transport.write(b'r')
        elif (data == code_for_granted) and (not check_for_user):
            a_level = 'a'
            access_task.set()
            if verbose_p:
                print("[ INFO ] Access granted")
        elif data == code_for_denied:
            a_level = 'd'
            access_task.set()
            if verbose_p:
                print("[ INFO ] Access denied")
        elif (data != "") and (data is not None) and check_for_user:
            # probably we have received user_id?
            if (data[:1] == code_for_granted) or (data[:1] == code_for_denied):
                if data == code_for_granted:
                    get_next_byte = True
                    if verbose_p:
                        print("[ INFO ] Access level code: granted for some user. Next stage - get user id which it was granted for.")
                elif data == code_for_denied:
                    a_level = 'd'
                    access_task.set()
                    if verbose_p:
                        print("[ INFO ] Access level code: \"{0}\"".format(a_level))

    def connection_lost(self, exc):
        global verbose_p, verbose_pp
        if verbose_p:
            print('[ INFO ] port closed')
        self.transport.loop.stop()

    def pause_writing(self):
        global verbose_p, verbose_pp
        if verbose_p:
            print('[ INFO ] pause writing')
            print(self.transport.get_write_buffer_size())

    def resume_writing(self):
        global verbose_p, verbose_pp
        if verbose_p:
            print(self.transport.get_write_buffer_size())
            print('[ INFO ] resume writing')


async def access_verified(loop):
    global timeout_for_verification
    with contextlib.suppress(asyncio.TimeoutError):
        await asyncio.wait_for(access_task.wait(), timeout_for_verification)

def check_user_match(user_system_name, board_user_id):
    global users_list, verbose_p, verbose_pp
    board_user_id = int(board_user_id)
    if users_list is not None:
        if user_system_name in users_list:
            if verbose_pp:
                print("[ INFO ] User found in database. Checking if it is a match:", int(users_list[user_system_name]) == board_user_id)
            return int(users_list[user_system_name]) == board_user_id
    return False

if not device_exists(device_addr):
    print("[ ERROR ] Unfortunately the device was not found.")
    exit(1)

def main(argv):
    global check_for_user, verbose_p, verbose_pp, a_level, aceess_task, get_next_byte, users_list, config_filename
    if os.path.isfile(config_filename):
        config = configparser.ConfigParser()
        try:
            config.read(config_filename)
            if 'DEFAULT' in config:
                if 'verbose' in config['DEFAULT']:
                    verbose_p = config['DEFAULT']['verbose'] == 'yes'
                if 'veryVerbose' in config['DEFAULT']:
                    verbose_pp = config['DEFAULT']['veryVerbose'] == 'yes'
                if 'connectType' in config['DEFAULT']:
                    connect_type = config['DEFAULT']['connectType']
                if 'timeout' in config['DEFAULT']:
                    timeout_for_verification = int(config['DEFAULT']['timeout'])
            if 'RS232' in config:
                if 'deviceAddr' in config['RS232']:
                    device_addr = config['RS232']['deviceAddr']
        except Exception as e:
            print('[ ERROR ] Error parsing config.ini file. It exists but there is smth wrong with it. Error looks like this: ',e)
    if verbose_pp:
        print("[ INFO ] Verbosity level: additionally verbose.")
    if verbose_p:
        if not verbose_pp:
            print("[ INFO ] Verbosity level: verbose.")
        print("[ INFO ] Connection type:", connect_type)
        print("[ INFO ] Timeout:", timeout_for_verification, "seconds.")
        print("[ INFO ] RS232 device address:", device_addr)
    username = ""
    username_provided = False
    try:
       opts, args = getopt.getopt(argv,"ht:",["tuser="])
       for opt, arg in opts:
           if opt == '-h':
               print (os.path.basename(__file__),' -t <user>')
               sys.exit(0)
           elif opt in ("-t", "--tuser"):
               username = arg.strip()
               if username != "":
                   check_for_user = True
                   username_provided = True
    except getopt.GetoptError:
       pass
    if username_provided:
        if verbose_p:
            print("[ INFO ] Username to check: \"{0}\"".format(username))
        if os.path.isfile('users.ini'):
            users_config = configparser.ConfigParser()
            try:
                users_config.read('users.ini')
                if 'Users' not in users_config:
                    raise Exception("There is no \"Users\" section in the configuration.")
                users_list = users_config['Users']
            except Exception as e:
                print('[ ERROR ] Error parsing users.ini file. It exists but there is smth wrong with it. Error looks like this: ',e)
                exit(1)
    if connect_type == 'rs232':
        if verbose_p:
            print('[ INFO ] Connecting via RS232.')
        loop = asyncio.get_event_loop()
        coro = serial_asyncio.create_serial_connection(loop, OutputProtocol, device_addr, baudrate=baud_rate, timeout=conn_tout)
        transport, protocol = loop.run_until_complete(coro)
        try:
            loop.run_until_complete(access_verified(loop))
        finally:
        #    loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
        if a_level is None:
            if verbose_p:
                print("[ INFO ] Well, timeout happened.")
            exit(1)
        if a_level == 'd':
            if verbose_p:
                print("[ INFO ] Access was denied.")
            exit(1)
        if check_for_user and (not check_user_match(username, a_level)):
            if verbose_p:
                print("[ INFO ] Access was denied by verifying the user code.")
            exit(1)
        elif check_for_user:
            if verbose_p:
                print("[ INFO ] Access was granted for user \"{0}\"".format(username))
        elif not check_for_user:
            if a_level == 'a':
                if verbose_p:
                    print("[ INFO ] Access was granted without check for specific username.")
            else:
                if verbose_p:
                    print("[ INFO ] Access was denied without check for specific username.")
                exit(1)
        exit(0)

if __name__ == "__main__":
   main(sys.argv[1:])
exit(0)