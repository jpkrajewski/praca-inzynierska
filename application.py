from datetime import datetime as dt
from flask import Flask
from flask import request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, migrate
from flask_mqtt import Mqtt

SUBSCRIBE_TOPIC = 'krajewski/private/factory/'
MEASUREMENTS_COUNTER = 0
MEASUREMENTS_SAVE_ONE_PER = 50
DATETIME_FORMAT_API = '%Y-%m-%dT%H:%M:%S'

application = Flask(__name__)
application.debug = True
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
application.config['MQTT_BROKER_URL'] = 'broker.hivemq.com'  # use the free broker from HIVEMQ
application.config['MQTT_BROKER_PORT'] = 1883  # default port for non-tls connection
application.config['MQTT_USERNAME'] = ''  # set the username here if you need authentication for the broker
application.config['MQTT_PASSWORD'] = ''  # set the password here if the broker demands authentication
application.config['MQTT_KEEPALIVE'] = 5  # set the time interval for sending a ping to the broker to 60 seconds
application.config['MQTT_TLS_ENABLED'] = False  # set TLS to disabled for testing purposes

db = SQLAlchemy(application)
migrate = Migrate(application, db)
mqtt = Mqtt(application)

class Measurement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    machine = db.Column(db.String(50), unique=False, nullable=False)
    device = db.Column(db.String(50), unique=False, nullable=False)
    state = db.Column(db.String(10), unique=False, nullable=False)
    unit = db.Column(db.String(20), unique=False, nullable=False)
    value = db.Column(db.Integer, unique=False, nullable=False)
    datetime = db.Column(db.DateTime, unique=False, nullable=False)

    def to_dict(self):
        return dict(id=self.id,
                    machine=self.machine,
                    device=self.device,
                    state=self.state,
                    unit=self.unit,
                    value=str(self.value),
                    datetime=str(self.datetime)
                    )


def decode_to_dict(message, now):
    array = message.split(' ')
    

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe(SUBSCRIBE_TOPIC)


@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    now = dt.now()
    global MEASUREMENTS_COUNTER
    MEASUREMENTS_COUNTER += 1
    if MEASUREMENTS_COUNTER == MEASUREMENTS_SAVE_ONE_PER:
        MEASUREMENTS_COUNTER = 0
        decode_to_dict(message=message.payload.decode('utf-8'), now=now)
        mes = Measurement(machine='test',
                          state='on',
                          unit='f',
                          value=32,
                          datetime=dt.now())
        db.session.add(mes)
        db.session.commit()


@application.route("/api/measurements")
def measurements_list():
    measurements = Measurement.query.all()
    json_measurnemts = []
    for meas in measurements:
        json_measurnemts.append(meas.to_dict())
    return jsonify(json_measurnemts)


@application.route('/api/measurements/<string:_from>/<string:to>', methods=['GET'])
def measurements_by_date(_from, to):
    _from = dt.strptime(_from, DATETIME_FORMAT_API)
    to = dt.strptime(to, DATETIME_FORMAT_API)
    json_mes = []
    mes_query = Measurement.query.filter(Measurement.datetime.between(_from, to)).all()

    for mes in mes_query:
        json_mes.append(mes.to_dict())

    return jsonify({'measurments': json_mes, 'statuscode': 200})


@application.route('/api/measurements/<int:id>', methods=['GET'])
def measurements_detail(id):
    return jsonify(Measurement.query.get(id).to_dict())


@application.route("/")
def hello_world():
   return 'Hello World!'


if __name__ == '__main__':
    application.run()
