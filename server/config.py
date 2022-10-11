import json
from abc import ABC, abstractmethod

FILE_PATH = 'config.json'

class Parser(ABC):
    @abstractmethod
    def parse(self, path):
        ...

class JSONParser(Parser):
    def parse(self, file):
        return json.load(file)

class Singleton:
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

class Config(Singleton):
    _data = None
    
    def __init__(self, parser:Parser, path:str=FILE_PATH):
        if self._data is None:
            with open(path, 'r') as file:
                self._data = parser.parse(file)

    @property
    def data(self):
        return self._data
