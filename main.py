import utime as time
import ujson as json
import usocket as socket
import network
import machine
from machine import Pin

def http_get(url):
    _, _, host_port, path = url.split('/', 3)
    host, port = host_port.split(':')
    addr = socket.getaddrinfo(host, int(port))[0][-1]
    s = socket.socket()
    s.connect(addr)
    req = 'GET /%s HTTP/1.0\r\nHost: %s\r\n\r\n' % (path, host)
    print(req)
    s.send(bytes(req, 'utf8'))
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
    # Hold GPIO2 low to keep board powered on via MOSFET
    print("keeping power on...")
    pin = Pin(2, Pin.OUT, value=0)
    print("running...")
    run()
finally:
    # set GPIO2 high to switch off board via MOSFET
    print("powering down...")
    pin.high()
    print("Sleeping...")
    time.sleep(5)
    machine.deepsleep()
