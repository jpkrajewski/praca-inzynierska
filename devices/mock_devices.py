from enum import IntEnum
from random import random, choice, randint

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
    r = randint(699, 703)
    if mode == LightMode.RED:
        return f'{r}-RED'
    if mode == LightMode.GREEN:
        return f'{r}-GREEN'
    if mode == LightMode.BLUE:
        return f'{r}-BLUE'
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
        return str(randint(5976, 6452)) 
    if mode == FanMode.FAST:
        return str(randint(9763, 12234)) 
    if mode == FanMode.SLOW:
        return str(randint(2364, 3452)) 
    raise ValueError('Invalid mode')

def generate_alarm_value(self, _) -> str:
    return choice(['ON', 'OFF'])

class BaseDevice:
    """
        Base device class
        Implements given generator strategy
    """
    _unit = None
    _value_generator = None

    def __init__(self, topic:str, mode:int) -> None:
        self._topic = topic
        self.mode = mode

    @property
    def info(self) -> str:
        return f'{self._get_unit()}/{self._value_generator(self.mode)}'

    @property
    def topic(self) -> str:
        return self._topic

    @property
    def mode(self) -> int:
        return self._mode

    @mode.setter
    def mode(self, value) :
        self._mode = value

    def _get_unit(self):
        return self._unit[self.mode]

    def __str__(self) -> str:
        return f'{self.topic}: {self.mode}, {self._get_unit()}'

class Thermometer(BaseDevice):
    _unit = ['CELCIUS', 'FAHRENHEIT', 'KELVIN']
    _value_generator = generate_thermometer_value

class Saw(BaseDevice):
    _unit = ['RPM']
    _value_generator = generate_chainsaw_value

    def _get_unit(self):
        return self._unit[0]

class Sensor(BaseDevice):
    _unit = ['DETECTED']
    _value_generator = generate_sensor_value

    def _get_unit(self):
        return self._unit[0]

class Fan(BaseDevice):
    _unit = ['RPM']
    _value_generator = generate_fan_value

    def _get_unit(self):
        return self._unit[0]

class Light(BaseDevice):
    _unit = ['LUMEN']
    _value_generator = generate_light_value

    def _get_unit(self):
        return self._unit[0]

class Alarm(BaseDevice):
    _unit = ['LOUD', 'SILENT']
    _value_generator = generate_alarm_value

    def _get_unit(self):
        if self.mode == 2:
            return self._unit[0]
        return self._unit[self.mode]

class DeviceFactory:
    """Factory for devices"""
    _scope = ['Thermometer', 'Sensor', 'Saw', 'Fan', 'Light', 'Alarm']
    def __init__(self, devices: list):
        self.devices = devices
    
    def _create(self, type:str, topic:str, mode:int) -> BaseDevice:
        if type in self._scope:
            return globals()[type](topic, mode)
        raise ValueError(f'Unknown device type {type}')

    def create_devices(self) -> list:
        return [self._create(**device) for device in self.devices]

            

        




