from machine import Pin,UART
import time
# config
led_pin = 8
rs232_tx_pin = 10
rs232_rx_pin = 9
board_tx_pin = 21
board_rx_pin = 20
request_access_code = b'r'
ping_code = b't'
access_granted_code = b'a'
access_denied_code = b'd'
baud_rate_rs232 = 9600
baud_rate_board = 115200
UART_IFACE_NO = 1
sleep_delay_msec = 1000
stops_for_rs232 = 2
stops_for_board = 1
bits_rs232 = 8
bits_board = 8
parity_rs232 = None
parity_board = None
sleep_after_board_cmd_ms = 100
additional_wait_for_board_response_ms = 1000
long_additional_wait_for_board_response_ms = 800
wait_for_face_recognition_ms = 4000
wait_for_face_recognition_attempt_ms = 100
talkative = True
display_on_during_auth = True
display_on_off_attempts = 3
lights_on_during_auth = False
lights_on_off_attempts = 3
board_startup_delay_ms = 1000
init_board_display_attempts_num = 3
init_board_display_attempts_delay_ms = 1000
try:
    from board_config import *
except ImportError:
    pass
# EOF config

def send_board_command(uuart, cmd, cmdarg=None, wait_for_response=False, sleep_after_board_command_ms=100,add_wait_for_board_response_ms=300):
    cmd_start_recognition = [b'\xEF', b'\xAA', b'\x12', b'\x00', b'\x00', b'\x00', b'\x00', b'\x12']
    cmd_register_face =     [b'\xEF', b'\xAA', b'\x13', b'\x00', b'\x00', b'\x00', b'\x00', b'\x13']
    cmd_delete_user = 		[b'\xEF', b'\xAA', b'\x20', b'\x00', b'\x00', b'\x00', b'\x02'] # XX YY; xx yy = 2 byte id
    cmd_delete_all_users = 	[b'\xEF', b'\xAA', b'\x21', b'\x00', b'\x00', b'\x00', b'\x00', b'\x21']
    cmd_backlight_off = 	[b'\xEF', b'\xAA', b'\xC0', b'\x00', b'\x00', b'\x00', b'\x01', b'\x00', b'\xC1']
    cmd_backlight_on = 		[b'\xEF', b'\xAA', b'\xC0', b'\x00', b'\x00', b'\x00', b'\x01', b'\x01', b'\xC2']
    cmd_display_off = 		[b'\xEF', b'\xAA', b'\xC1', b'\x00', b'\x00', b'\x00', b'\x01', b'\x00', b'\xC2']
    cmd_display_on = 		[b'\xEF', b'\xAA', b'\xC1', b'\x00', b'\x00', b'\x00', b'\x01', b'\x01', b'\xC3']
    cmd_light_off = 		[b'\xEF', b'\xAA', b'\xC2', b'\x00', b'\x00', b'\x00', b'\x01', b'\x00', b'\xC3']
    cmd_light_on = 			[b'\xEF', b'\xAA', b'\xC2', b'\x00', b'\x00', b'\x00', b'\x01', b'\x01', b'\xC4']
    found_command_list = []
    if cmd == 'display_off':
        found_command_list = cmd_display_off
    elif cmd == 'display_on':
        found_command_list = cmd_display_on
    elif cmd == 'backlight_on':
        found_command_list = cmd_backlight_on
    elif cmd == 'backlight_off':
        found_command_list = cmd_backlight_off
    elif cmd == 'light_on':
        found_command_list = cmd_light_on
    elif cmd == 'light_off':
        found_command_list = cmd_light_off
    elif cmd == 'register_face':
        found_command_list = cmd_register_face
    elif cmd == 'start_recognition':
        found_command_list = cmd_start_recognition
    elif cmd == 'delete_all_users':
        found_command_list = cmd_delete_all_users
    elif cmd == 'delete_user':
        found_command_list = cmd_delete_user
        found_command_list.append(cmdarg) # should be a 2-byte list with user id
    for c in found_command_list:
        uuart.write(c)
    time.sleep_ms(sleep_after_board_command_ms)
    if wait_for_response:
        if uuart.any():
            return True
        else:
            time.sleep_ms(add_wait_for_board_response_ms)
            return not not uuart.any() # rather stupid way to convert to boolean.
    return True

def get_board_output(uuart, prnt=False):
    if uuart.any():
        rcvd = uuart.read()
        if(prnt):
            print('Received response: ', rcvd)
        return rcvd
    return ""

def raise_err(msg):
    print("[ ERROR ]",msg)

def init_board_display(uuart, sleep_after_board_command_ms,add_wait_for_board_response_ms, chatterbox):
    init_status = False
    if send_board_command(uuart, 'display_off', None, True, sleep_after_board_command_ms,add_wait_for_board_response_ms):
        board_output = get_board_output(uuart, chatterbox)
        init_status = True
    else:
        raise_err("No response from board (tried to switch off display)!") 
    if send_board_command(uuart, 'light_off', None, True, sleep_after_board_command_ms, add_wait_for_board_response_ms):
        board_output = get_board_output(uuart, chatterbox)
        init_status = init_status and True
    else:
        raise_err("No response from board (tried to switch off lights)!") 
    if init_status:
        if chatterbox:
            print("Response from board received successfully. Init complete.")
    return init_status

def init_board(iface_no,b_rate,b_tx_pin,b_rx_pin,bits_b,parity_b,stops_for_b,chatterbox, sleep_after_board_command_ms,add_wait_for_board_response_ms,init_board_display_attempts, init_board_display_attempts_d_ms):
    init_status = False
    if chatterbox:
        print("Init board....")
    for i in range(init_board_display_attempts):
        uart2 = UART(iface_no, baudrate=b_rate, tx=Pin(b_tx_pin), rx=Pin(b_rx_pin))
        uart2.init(bits=bits_b, parity=parity_b, stop=stops_for_b)
        init_status = init_status or init_board_display(uart2, sleep_after_board_command_ms,add_wait_for_board_response_ms, chatterbox)
        uart2.deinit()
        time.sleep_ms(init_board_display_attempts_d_ms)
    return init_status

def check_auth(iface_no,b_rate,b_tx_pin,b_rx_pin,bits_b,parity_b,stops_for_b,chatterbox, w_for_face_recognition_attempt_ms, w_for_face_recognition_ms, turn_on_lights_when_verifying=False, l_attempts=2, turn_on_display_when_verifying=False, dspl_attempts=2, sleep_after_board_command_ms=100,add_wait_for_board_response_ms=300):
    no_face_code = b'\xEF\xAA\x00\x00\x00\x00\x02\x12\x01\x15'
    start_recognition_code = b'\xef\xaa\x00\x00\x00\x00\x02\xc1\x00\xc3'
    uart2 = UART(iface_no, baudrate=b_rate, tx=Pin(b_tx_pin), rx=Pin(b_rx_pin))
    uart2.init(bits=bits_b, parity=parity_b, stop=stops_for_b)
    send_board_command(uart2, 'start_recognition', None, False)
    if turn_on_display_when_verifying:
        for i in range(dspl_attempts):
            if not send_board_command(uart2, 'display_on', None, True, sleep_after_board_command_ms,add_wait_for_board_response_ms):
                raise_err("No response from board (tried to turn on display)!")
            else:
                break
    if turn_on_lights_when_verifying:
        for i in range(l_attempts):
            if not send_board_command(uart2, 'light_on', None, True, sleep_after_board_command_ms,add_wait_for_board_response_ms):
                raise_err("No response from board (tried to turn on lights)!")
            else:
                break
    # The verification itself
    access_receive_status = False
    board_output = ""
    deadline = time.ticks_add(time.ticks_ms(), w_for_face_recognition_ms)
    while (len(board_output) == 0) and (time.ticks_diff(deadline, time.ticks_ms()) > 0):
        board_output = get_board_output(uart2, chatterbox)
        if(len(board_output) > 0):
            if chatterbox:
                print("Output received: ", board_output)
            if (board_output == start_recognition_code):
                if chatterbox:
                    print("Start recognition code received. Ignoring.")
                board_output = ""
            elif (board_output == no_face_code):
                if chatterbox:
                    print("No user face detected!")
                board_output = ""
                send_board_command(uart2, 'start_recognition', None, False)
        time.sleep_ms(w_for_face_recognition_attempt_ms)
    # EOF verification
    if turn_on_display_when_verifying:
        for i in range(dspl_attempts):
            if not send_board_command(uart2, 'display_off', None, True, sleep_after_board_command_ms,add_wait_for_board_response_ms):
                raise_err("No response from board (tried to switch off display)!")
            else:
                break
    if turn_on_lights_when_verifying:
        for i in range(l_attempts):
            if not send_board_command(uart2, 'light_off', None, True, sleep_after_board_command_ms,add_wait_for_board_response_ms):
                raise_err("No response from board (tried to turn on lights)!")
            else:
                break
    uart2.deinit()
    return board_output


def init_rs232(iface_no,b_rate,b_tx_pin,b_rx_pin,bits_b,parity_b,stops_for_b,chatterbox):
    uuart = UART(iface_no, baudrate=b_rate, tx=Pin(b_tx_pin), rx=Pin(b_rx_pin))
    uuart.init(bits=bits_b, parity=parity_b, stop=stops_for_b)
    return uuart

def deinit_rs232(uuart):
    uuart.deinit()

def send_rs232_ping(uuart, rs232_ping_code):
    uuart.write(rs232_ping_code)

def check_get_read_rs232(uuart):
    d = None
    if uuart.any(): 
        d = uuart.read()
    return d

time.sleep_ms(board_startup_delay_ms)

board_initialization_status = init_board(UART_IFACE_NO,baud_rate_board,board_tx_pin,board_rx_pin,bits_board,parity_board,stops_for_board,talkative,sleep_after_board_cmd_ms,additional_wait_for_board_response_ms, init_board_display_attempts_num, init_board_display_attempts_delay_ms)

if talkative:
    print("Init board success: ", board_initialization_status)

uart = init_rs232(UART_IFACE_NO,baud_rate_rs232,rs232_tx_pin,rs232_rx_pin,bits_rs232,parity_rs232,stops_for_rs232,talkative)

led = Pin(led_pin, Pin.OUT)

while True:
    send_rs232_ping(uart,ping_code)
    data = check_get_read_rs232(uart)
    if data is not None:
        if data==request_access_code:
            # Check access
            deinit_rs232(uart)
            access_received = access_denied_code
            user_id_detected = check_auth(UART_IFACE_NO,baud_rate_board,board_tx_pin,board_rx_pin,bits_board,parity_board,stops_for_board, talkative, wait_for_face_recognition_attempt_ms, wait_for_face_recognition_ms, lights_on_during_auth,lights_on_off_attempts, display_on_during_auth, display_on_off_attempts, sleep_after_board_cmd_ms,additional_wait_for_board_response_ms)
            if len(user_id_detected) > 0:
                access_received = access_granted_code
            uart = init_rs232(UART_IFACE_NO,baud_rate_rs232,rs232_tx_pin,rs232_rx_pin,bits_rs232,parity_rs232,stops_for_rs232,talkative)
            uart.write(access_received)
    time.sleep_ms(sleep_delay_msec)

