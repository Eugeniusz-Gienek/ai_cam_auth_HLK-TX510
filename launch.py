import os
import asyncio
import contextlib
import serial_asyncio

timeout_for_verification = 5
device_addr = '/dev/ttyUSB0' # Com port-connected
baud_rate = 9600
conn_tout = 1
code_for_granted = b'a'
code_for_denied = b'd'
code_for_ping = b't'

verbose_p = False
verbose_pp = False
a_level = None
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
        self.transport = transport
        if verbose_p:
            print('port opened', transport)
        transport.serial.rts = False  # You can manipulate Serial object via transport
        transport.write(b'r')  # Write serial data via transport

    def data_received(self, data):
        global a_level, code_for_granted, code_for_denied, code_for_ping
        if verbose_pp:
            print('data received', repr(data))
        if data == code_for_ping:
            transport.write(b'r')
        elif data == code_for_granted:
            a_level = 'a'
            access_task.set()
            print("granted")
        elif data == code_for_denied:
            a_level = 'd'
            access_task.set()
            print("denied")

    def connection_lost(self, exc):
        if verbose_p:
            print('port closed')
        self.transport.loop.stop()

    def pause_writing(self):
        if verbose_p:
            print('pause writing')
            print(self.transport.get_write_buffer_size())

    def resume_writing(self):
        if verbose_p:
            print(self.transport.get_write_buffer_size())
            print('resume writing')


async def access_verified(loop):
    global timeout_for_verification
    with contextlib.suppress(asyncio.TimeoutError):
        await asyncio.wait_for(access_task.wait(), timeout_for_verification)

if not device_exists(device_addr):
    print("Unfortunately the device was not found.")
    exit(1)

loop = asyncio.get_event_loop()
coro = serial_asyncio.create_serial_connection(loop, OutputProtocol, device_addr, baudrate=baud_rate, timeout=conn_tout)
transport, protocol = loop.run_until_complete(coro)

try:
    loop.run_until_complete(access_verified(loop))
finally:
#    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()
if a_level is None:
    print("timeout")
    exit(1)
if a_level == 'd':
    exit(1)
exit(0)
