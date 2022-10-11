from kivy.app import App
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.widget import Widget
import paho.mqtt.client as mqtt


class AnchorLayoutEx(AnchorLayout):
    pass


class BoxLayoutEx(BoxLayout):
    pass


class MainWidget(Widget):
    pass


class MachinePulpitApp(App):
    def on_start(self):

        def on_connect(client, userdata, flags, rc):
            client.subscribe('krajewski/private/factory/')

        def on_message(client, userdata, msg):
            msg.payload = msg.payload.decode("utf-8")
            print("[INFO   ] [MQTT        ] topic: " + msg.topic + " msg: " + msg.payload)

        client = mqtt.Client(client_id="kivy-client", clean_session=True)
        client.on_connect = on_connect
        client.on_message = on_message
        client.connect("broker.hivemq.com", 1883, keepalive=60, bind_address="")
        client.loop_start()  # start loop to process callbacks! (new thread!)


MachinePulpitApp().run()
