import random
import requests
import time
from paho.mqtt.client import Client
from mock_devices import DeviceFactory

# API_CONF_URL = 'http://13.42.63.86/api/config'
API_CONF_URL = 'http://127.0.0.1:5000/api/config'

response = requests.get(API_CONF_URL)
if response.status_code != 200:
    raise ConnectionError(f'There was error during downloading config from API. Server responsed with status {response.status_code}')
config = response.json()
simulated_devices = DeviceFactory(config['devices']).create_devices()

def on_connect(client, userdata, flags, rc):
    for device in simulated_devices:
        print('Subscribing to topic:', device.topic)
        client.subscribe(device.topic)

def on_message(client, userdata, msg):
    print('Message received:', msg.payload.decode('utf-8'))
    payload = msg.payload.decode('utf-8')
    if payload[:4] in 'mode':
        for device in simulated_devices:
            if device.topic == msg.topic:
                field, value = payload.split('=')
                device.mode = int(value)
                print(device)

client = Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(config['host'], config['port'])
client.loop_start()

while True:
    for device in simulated_devices:
        client.publish(device.topic, device.info)
        print('Sending data:', device.topic, device.info, device.mode)
    time.sleep(random.randint(1, 2))
