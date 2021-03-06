import utime as time
script_start = time.ticks_ms()

import ujson as json
import usocket as socket
import network
import machine
from machine import Pin

sleep_when_done = False

REQUEST_TIMEOUT = 5000


def finish():
    # To prevent sleeping, connect GPIO0 to GND via 10K resistor
    pin = Pin(0, Pin.IN)
    sleep = pin.value() == 1

    print("Total runtime: {}ms".format(time.ticks_ms() - script_start))

    if sleep:
        print("Sleeping...")
        machine.deepsleep()
    else:
        print("Staying awake.")


def http_get(url):
    _, _, host_port, path = url.split('/', 3)
    host, port = host_port.split(':')
    addr = socket.getaddrinfo(host, int(port))[0][-1]
    s = socket.socket()
    s.connect(addr)
    req = 'GET /{} HTTP/1.0\r\nHost: {}\r\n\r\n'.format(path, host)
    print(req)
    s.send(bytes(req, 'utf8'))
    start = time.ticks_ms()
    timer = 0
    response = bytes()
    print('awaiting response...', end='')
    while True:
        print('.', end='')
        data = s.recv(100)
        if not data or timer > REQUEST_TIMEOUT:
            break
        timer = time.ticks_ms() - start
        response += data
    print('\n\n' + response.decode('utf8'))
    s.close()


def run():
    # load config
    with open('config.json', 'r') as config_file:
       config = json.load(config_file)

    # turn led on
    led = Pin(2, Pin.OUT, value=0)

    print('starting up...')
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    static = None

    try:
        with open('static.cfg', 'r') as static_cfg:
            print('found static config')
            static = static_cfg.read().strip().split('\n')
            if len(static) < 4:
                static = None
    except OSError:
        pass

    if static:
        print('using static config: ', static)
        wlan.ifconfig(static)

    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect(config['ssid'], config['password'])
        while not wlan.isconnected():
            pass

    if static is None:
        # save wifi config for faster reconnection
        ifconfig = '\n'.join(wlan.ifconfig())
        with open('static.cfg', 'w') as static_cfg:
            print('Saving static config')
            static_cfg.write(ifconfig)

    http_get(config['url'])

    # turn led off
    led.high()


try:
    run()
finally:
    finish()
