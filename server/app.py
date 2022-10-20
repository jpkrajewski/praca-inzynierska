from datetime import datetime as dt
import dateutil.relativedelta
from config import Config, JSONParser
from flask import Flask
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_mqtt import Mqtt

config = Config(parser=JSONParser()).data
app = Flask(__name__)
app.debug = config['DEBUG']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = config['DATABASE_URI']
if app.debug:
    app.config['SQLALCHEMY_DATABASE_URI'] = config['DATABASE_TESTING']
app.config['MQTT_BROKER_URL'] = config['MQTT_BROKER_URL']
app.config['MQTT_BROKER_PORT'] = config['MQTT_BROKER_PORT']
app.config['MQTT_USERNAME'] = ''
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_KEEPALIVE'] = 5
app.config['MQTT_TLS_ENABLED'] = False

MEASUREMENTS_COUNTER = 0
MEASUREMENTS_SAVE_ONE_PER = config['MEASUREMENTS_SAVE_ONE_PER']
DATETIME_FORMAT_API = '%Y-%m-%dT%H:%M:%S'

db = SQLAlchemy(app)
mqtt = Mqtt(app)

class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(50), unique=False, nullable=False)
    token = db.Column(db.String(50), unique=True, nullable=False)
    model = db.Column(db.String(50), unique=False, nullable=False)
    type = db.Column(db.String(50), unique=False, nullable=False)
    mode = db.Column(db.Integer, unique=False, nullable=False)
    measurement = db.relationship('Measurement', backref='Device')

    @property
    def config_dict(self):
        return dict(topic=f'{self.topic}{self.token}',
                    type=self.type,
                    mode=self.mode)

    @property
    def serialized(self):
        return dict(topic=f'{self.topic}{self.token}',
                    type=self.type,
                    model=self.model,
                    mode=self.mode)
    
    @property
    def full_topic(self):
        return f'{self.topic}{self.token}'

    def __str__(self) -> str:
        return f'{self.topic}{self.token}'

class Measurement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unit = db.Column(db.String(20), unique=False, nullable=False)
    value = db.Column(db.String(40), unique=False, nullable=False)
    datetime = db.Column(db.DateTime, unique=False, nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'))

    @property
    def serialized(self):
        value = self.get_value_to_serialize()
        if isinstance(value, float):
            value = round(value, 5)
        return dict(unit=self.unit,
                    value=value,
                    datetime=self.datetime.strftime(DATETIME_FORMAT_API))

    def get_value_to_serialize(self):
        if self.unit == 'RPM':
            return float(self.value)
        
        if self.unit in ['DETECTED', 'LUMEN', 'LOUD', 'SILENT']:
            return self.value

        if self.unit == 'CELSIUS':
            return float(self.value)

        if self.unit == 'FAHRENHEIT':
            return float(self.value)

        if self.unit == 'KELVIN':
            return float(self.value)

    def get_value(self):
        if self.unit == 'RPM':
            return float(self.value)
        
        if self.unit in ['DETECTED', 'LUMEN', 'LOUD', 'SILENT']:
            return self.value

        if self.unit == 'CELCIUS':
            return float(self.value)

        if self.unit == 'FAHRENHEIT':
            return (float(self.value) - 32) / 1.8

        if self.unit == 'KELVIN':
            return float(self.value) - 273.15

    def __str__(self) -> str:
        return f'{self.unit}: {self.value} {self.datetime}'

def decode_to_dict(message, now):
    values = message.split('/') + [now]
    keys = ('unit', 'value', 'datetime')
    return {x[0]:x[1] for x in zip(keys, values)}

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    devices = Device.query.all()
    for d in devices:
        mqtt.subscribe(d.full_topic)

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    device = Device.query.filter_by(token=message.topic.split('/')[-1]).first()
    if 'mode' in message.payload.decode('utf-8'):
        return
    else:
        global MEASUREMENTS_COUNTER
        MEASUREMENTS_COUNTER += 1
        if MEASUREMENTS_COUNTER == MEASUREMENTS_SAVE_ONE_PER:
            MEASUREMENTS_COUNTER = 0
            measurement = Measurement(**decode_to_dict(message=message.payload.decode('utf-8'), now=dt.now()), device_id=device.id)
            db.session.add(measurement)
            db.session.commit()

def _get_devices():
    return [d.config_dict for d in Device.query.all()]

def _get_devices_gui():
    return [d.serialized for d in Device.query.all()]

def _get_distinct_topics():
    return [d[0] for d in db.session.query(Device.topic).distinct()]

@app.route('/api/config/', methods=['GET'])
def get_config():
    return jsonify({'host': config['MQTT_BROKER_URL'],
                    'port': int(config['MQTT_BROKER_PORT']),
                    'devices': _get_devices()})

@app.route('/api/config-gui/', methods=['GET'])
def get_config_gui():
    return jsonify({'host': config['MQTT_BROKER_URL'],
                    'port': int(config['MQTT_BROKER_PORT']),
                    'devices': _get_devices_gui(),
                    'topics': _get_distinct_topics()})

@app.route('/api/device/<string:token>/measurements/today/', methods=['GET'])
def device_measurements_today(token):
    device = Device.query.filter_by(token=token).first_or_404()
    day_start = dt.now().replace(hour=0, minute=0, second=0, microsecond=0)
    measurements = Measurement.query.filter_by(device_id=device.id).filter(Measurement.datetime >= day_start, Measurement.unit != 'mode').all()
    print(measurements)
    modes = Measurement.query.filter_by(device_id=device.id).filter(Measurement.datetime >= day_start, Measurement.unit == 'mode').limit(20).all()
    worktime = Measurement.query.filter_by(device_id=device.id).order_by(Measurement.datetime.asc()).first()
    dt1 = dt.now() 
    dt2 = worktime.datetime
    rd = dateutil.relativedelta.relativedelta(dt1, dt2)
    print(f'{rd.months} months, {rd.days} days, {rd.hours} hours, {rd.minutes} minutes')
    if len(measurements) == 0 or isinstance(measurements[0].get_value(), str):
        avg = 'N/A'
        max_v = 'N/A'
        min_v = 'N/A'
    else:
        avg = sum([m.get_value() for m in measurements]) / len(measurements)
        max_v = max([m.get_value() for m in measurements])
        min_v = min([m.get_value() for m in measurements])

    return jsonify({'device': device.serialized, 
                    'measurments': [m.serialized for m in measurements[:20]],
                    'modes': [m.serialized for m in modes],
                    'avg': avg,
                    'max': max_v,
                    'min': min_v,
                    'worktime': f'{rd.months} months, {rd.days} days, {rd.hours} hours, {rd.minutes} minutes'})

@app.route('/api/device/<string:token>/measurements/date/<string:_from>/<string:to>/', methods=['GET'])
def device_measurements_by_date(token:str, _from:str, to:str):
    device = Device.query.filter_by(token=token).first_or_404()
    _from = dt.strptime(_from, DATETIME_FORMAT_API)
    to = dt.strptime(to, DATETIME_FORMAT_API)
    measurements = Measurement.query.filter_by(device_id=device.id).filter(Measurement.datetime.between(_from, to)).all()
    return jsonify({'device': device.serialized, 'measurments': [m.serialized for m in measurements]}, 200)

@app.route('/api/device/<string:token>/', methods=['GET'])
def device_info(token:str):
    device = Device.query.filter_by(token=token).first_or_404()
    return jsonify({'device': device.serialized})

@app.route('/api/device/<string:token>/mode/<int:mode>/', methods=['POST'])
def change_mode(token:str, mode:int):
    if mode not in (0, 1, 2):
        return jsonify({'message': 'Mode must be 0, 1 or 2'}), 400
    device = device = Device.query.filter_by(token=token).first_or_404()
    device.mode = mode
    measurement = Measurement(unit='mode', value=mode, datetime=dt.now(), device_id=device.id)
    db.session.add(measurement)
    db.session.commit()
    mqtt.publish(topic=device.full_topic, payload=f'mode={mode}', qos=2)
    return jsonify({'device': token, 'mode': mode})

@app.route("/")
def hello_world():
    return jsonify('Hello World!')

