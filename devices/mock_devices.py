from enum import IntEnum
from random import random, choice

class AlarmMode(IntEnum):
    LOUD = 0
    QUIET = 1

class ThermometerMode(IntEnum):
    C = 0
    F = 1
    K = 2

class FanMode(IntEnum):
    DEFAULT = 0
    FAST = 1
    SLOW = 2

class LightMode(IntEnum):
    RED = 0
    GREEN = 1
    BLUE = 2

def generate_light_value(self, mode) -> str:
    if mode == LightMode.RED:
        return '700-RED'
    if mode == LightMode.GREEN:
        return '700-GREEN'
    if mode == LightMode.BLUE:
        return '700-BLUE'
    raise ValueError('Invalid mode')
     
def generate_thermometer_value(self, mode) -> str:
    c = random() * 5 + 30
    if mode == ThermometerMode.C:
        return str(c)
    if mode == ThermometerMode.F:
        return str(c * 9 / 5 + 32)
    if mode == ThermometerMode.K:
        return str(c + 273.15)
    raise ValueError('Invalid mode')

def generate_sensor_value(self, _) -> str:
    return choice(['YES', 'NO'])

def generate_chainsaw_value(self, _) -> str:
    return choice(['7000', '0'])

def generate_fan_value(self, mode) -> str:
    if mode == FanMode.DEFAULT:
        return '6000'
    if mode == FanMode.FAST:
        return '10000'
    if mode == FanMode.SLOW:
        return '3000'
    raise ValueError('Invalid mode')

def generate_alarm_value(self, mode) -> str:
    return choice(['ON', 'OFF'])

class BaseDevice:
    """
        Base device class
        Implements given generator strategy
    """
    _unit = None
    _value_generator = None

    def __init__(self, topic:str,  state:str="ON", mode:int=0):
        self._topic = topic
        self._state = state
        self.mode = mode

    @property
    def info(self):
        return f'{self._get_unit()}/{self._value_generator(self.mode)}'

    @property
    def topic(self):
        return self._topic

    def _get_unit(self):
        return self._unit[self.mode]

class Thermometer(BaseDevice):
    _unit = ['CELCIUS', 'FAHRENHEIT', 'KELVIN']
    _value_generator = generate_thermometer_value

class Saw(BaseDevice):
    _unit = ['RPM']
    _value_generator = generate_chainsaw_value

class Sensor(BaseDevice):
    _unit = ['DETECTED']
    _value_generator = generate_sensor_value

class Fan(BaseDevice):
    _unit = ['RPM']
    _value_generator = generate_fan_value

class Light(BaseDevice):
    _unit = ['LUMEN']
    _value_generator = generate_light_value

class Alarm(BaseDevice):
    _unit = ['LOUD', 'SILENT']
    _value_generator = generate_alarm_value

class DeviceFactory:
    """Factory for devices"""
    _scope = ['Thermometer', 'Sensor', 'Saw', 'Fan', 'Light', 'Alarm']
    def __init__(self, devices: list):
        self.devices = devices
    
    def _create(self, type: str, topic: str) -> BaseDevice:
        if type in self._scope:
            return globals()[type](topic)
        raise ValueError(f'Unknown device type {type}')

    def create_devices(self) -> list:
        return [self._create(**device) for device in self.devices]

            

        




