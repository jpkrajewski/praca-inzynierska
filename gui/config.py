import requests

API_URL = 'http://127.0.0.1:5000'
API_CONF_URL = API_URL + '/api/config-gui/'

class Singleton:
    _instance = None
    _data = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__new__(cls, *args, **kwargs)
        return cls._instance

class Config(Singleton):
    def __init__(self):
        if self._data is None:
            response = requests.get(API_CONF_URL)
            if response.status_code != 200:
                raise ConnectionError(f'There was error during downloading config from API. Server responsed with status {response.status_code}')
            self._data = response.json()
            self._data['topics_devices'] = self._transform(self._data)

    def _transform(self, data) -> dict[str, dict[str, str]]:
        """Transforms data from API to dict with topics keys and devices values"""
        topics = {topic:[] for topic in data['topics']}
        for device in data['devices']:
            # device['topic'] -> "krajewski/machine/1/c1f483939dcd36312112"
            topic_end_index = device['topic'].rfind('/') + 1
            device['topic_short'] = device['topic'][topic_end_index:]
            topics[device['topic'][:topic_end_index]].append(device)
        return topics
        
    @property
    def topics_devices(self):
        return self._data['topics_devices']

    @property
    def port(self):
        return self._data['port']

    @property
    def host(self):
        return self._data['host']

    @property
    def devices(self):
        return self._data['devices']

    @property
    def topics(self):
        return self._data['topics']

    @property
    def change_mode(self) -> str:
        return API_URL + '/api/device/{}/mode/{}/'

    @property
    def show_device_measurements(self) -> str:
        return API_URL + '/api/device/{}/measurements/today/'
            