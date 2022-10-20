from tkinter import font
from turtle import Screen
from kivy.app import App
from kivy.uix.stacklayout import StackLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen, WipeTransition
from kivy.graphics import Color, Rectangle
import paho.mqtt.client as mqtt
from config import Config
import requests

class DeviceInfoController:
    """Changes info about device on the screen, 
    sets mode and sends it to the server"""
    _device_rows = {}
    _device_detail = []
    @classmethod
    def add_device(cls, key, mode, value, unit):
        cls._device_rows[key] = (mode, value, unit)

    @classmethod
    def update_row_info(cls, key, value, unit):
        cls._device_rows[key][1].text = value
        cls._device_rows[key][2].text = unit

    @classmethod
    def change_mode(cls, instance):
        instance.current_mode += 1
        if instance.current_mode == 3:
            instance.current_mode = 0
        request = config.change_mode.format(instance.topic_short, instance.current_mode)
        requests.post(request)
        cls._device_rows[instance.topic][0].text = f'Mode: {instance.current_mode}'

    @classmethod
    def change_screen_to_device_details(cls, instance):
        app = App.get_running_app()
        request = config.show_device_measurements.format(instance.short_topic)
        response = requests.get(request).json()
        print(response)

        cls._device_detail[0].text = f"[b]ID: {instance.short_topic}\nType: {response['device']['type']}\nModel: {instance.model}[/b]"
        cls._device_detail[1].text = '\n'.join([f"{measurement['datetime']} - {measurement['value']} {measurement['unit']}" for measurement in response['measurments']])
        cls._device_detail[2].text = '\n'.join([f"{measurement['datetime']} - {measurement['value']} {measurement['unit']}" for measurement in response['modes']])
        cls._device_detail[3].text = f"Average value\n{response['avg']}"
        cls._device_detail[4].text = f"Max value\n{response['max']}"
        cls._device_detail[5].text = f"Min value\n{response['min']}"
        cls._device_detail[6].text = f"Worktime\n{response['worktime']}"
        app.root.transition.direction = "left"
        app.root.current = 'device_details'

    @classmethod
    def set_device_detail_labels(cls, label_detail, label_measurements, label_modes, label_today_avg, 
        label_today_max, label_today_min, label_device_work_time):
        cls._device_detail = [label_detail, label_measurements, label_modes, label_today_avg, 
        label_today_max, label_today_min, label_device_work_time]


class DeviceLayoutFactory:
    """Factory for invidual device"""
    @staticmethod
    def create(device) -> Widget:
        layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=50)
        layout.add_widget(Label(text=device['model']))
        label_mode = Label(text=str(f"Mode: {device['mode']}"))
        label_value = Label(text='0')
        label_unit = Label(text='None')
        DeviceInfoController.add_device(device['topic'], label_mode, label_value, label_unit)
        layout.add_widget(label_mode)
        layout.add_widget(label_value)
        layout.add_widget(label_unit)
        btn_change_mode = Button(text='Change mode')
        btn_change_mode.topic_short = device['topic_short']
        btn_change_mode.topic = device['topic']
        btn_change_mode.current_mode = device['mode']
        btn_change_mode.bind(on_press=DeviceInfoController.change_mode)
        layout.add_widget(btn_change_mode)
        btn_show_details = Button(text='Details', on_press=DeviceInfoController.change_screen_to_device_details)
        btn_show_details.short_topic = device['topic_short']
        btn_show_details.model = device['model']
        layout.add_widget(btn_show_details)
        return layout

class MyLabel(Label):
   def on_size(self, *args):
      self.text_size = self.size

class DeviceDetailsScreen(Screen):
    """Screen with details about device"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        box_main = BoxLayout(orientation='vertical')
        box_main.add_widget(Button(text='Back to topic', on_press=self.back, size_hint=(0.16, None), height=50, font_size='20sp', 
            markup=True, background_color=(255, 0, 0, 1)))
        label_device = Label(text='', font_size='20sp', markup=True, size_hint=(1, 0.3))
        label_measurements = Label(text='', font_size='13sp', padding=(5,5))
        box_main.add_widget(label_device)
        box_lower = BoxLayout(orientation='horizontal', size_hint=(1, 0.7))
        box_lower_left = BoxLayout(orientation='vertical', size_hint=(0.3, 1))
        box_lower_left.add_widget(Label(text='Last 20 measurements', size_hint=(1, None), height=50, font_size='20sp'))
        box_lower_left.add_widget(label_measurements)
        box_lower_mid = BoxLayout(orientation='vertical', size_hint=(0.3, 1))
        box_lower_mid.add_widget(Label(text='Mode changes', size_hint=(1, None), height=50, font_size='20sp'))
        label_mode = Label(text='.....', font_size='13sp', padding=(5,5))
        box_lower_mid.add_widget(label_mode)
        box_lower_right = BoxLayout(orientation='vertical', size_hint=(0.4, 1))
        box_lower_right.add_widget(Label(text='Device stats', size_hint=(1, None), height=50, font_size='20sp'))
        labels = [MyLabel(text='Placeholder', size_hint=(0.7, 0.2), pos_hint={'center_x': 0.5}, font_size='17sp', halign="left", valign="middle") for _ in range(4)]
        for label in labels:
            box_lower_right.add_widget(label)
        box_lower.add_widget(box_lower_left)
        box_lower.add_widget(box_lower_mid)
        box_lower.add_widget(box_lower_right)
        box_main.add_widget(box_lower)
        DeviceInfoController.set_device_detail_labels(label_device, label_measurements, label_mode, *labels)
        self.add_widget(box_main)

    @staticmethod
    def back(instance):
        app = App.get_running_app()
        app.root.current = app.last_screen

class TopicDetailLayout(StackLayout):
    """Topic detail layout"""
    def __init__(self, topic, **kwargs):
        super(TopicDetailLayout, self).__init__(**kwargs)
        self.orientation = 'lr-tb'
        self.add_widget(Button(text=f'Menu', font_size='20sp', 
            size_hint=(0.1, None), height=50, on_press=self.change_screen_to_menu, background_color=(255, 0, 0, 1)))
        self.add_widget(Label(text=f'[b]Topic: {topic}[/b]', font_size='20sp', 
            markup=True, size_hint=(1, None), height=50))

    @staticmethod
    def change_screen_to_menu(instance):
        app = App.get_running_app()
        app.root.transition.direction = "right"
        app.root.current = "menu"

class TopicDetailScreen(Screen):
    """Screen with details about topic"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_leave(self, *args):
        app = App.get_running_app()
        app.root.transition.direction = "right"
        app.last_screen = self.name

class MenuLayout(GridLayout):
    """Layout for screen with topics"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rows = 2
        print(config.topics)
        for topic in config.topics:
            button = Button(text=f'Topic: {topic}', font_size='30sp')
            button.topic = topic
            button.bind(on_press=self.change_screen)
            self.add_widget(button)

    @staticmethod
    def change_screen(instance):
        app = App.get_running_app()
        app.root.transition.direction = "left"
        app.root.current = instance.topic

class MenuScreen(Screen):
    """Screen with topics"""
    def __init__(self, **kwargs):
        super(MenuScreen, self).__init__(**kwargs)
        self.add_widget(MenuLayout())

class MachinePulpitApp(App):
    """Main class for the application."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.last_screen = ''

    def build(self):
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name='menu'))
        print(sm.screen_names)
        for topic, devices in config.topics_devices.items():
            topic_detail_screen = TopicDetailScreen(name=topic)
            topic_detail = TopicDetailLayout(topic)
            for device in devices:
                topic_detail.add_widget(DeviceLayoutFactory().create(device))
            topic_detail_screen.add_widget(topic_detail)
            sm.add_widget(topic_detail_screen)
        sm.add_widget(DeviceDetailsScreen(name='device_details'))
        return sm

    def on_start(self):
        def on_connect(client, userdata, flags, rc):
            """The callback for when the client receives a CONNACK response from the server."""
            for device in config.devices:
                client.subscribe(device['topic'])

        def on_message(client, userdata, msg):
            """Callback for receiving messages from the MQTT server."""
            msg.payload = msg.payload.decode("utf-8")
            if msg.payload[:4] == 'mode':
                pass
            else:
                unit, value = msg.payload.split('/')
                DeviceInfoController.update_row_info(msg.topic, value, unit)
            print("[INFO   ] [MQTT        ] topic: " + msg.topic + " msg: " + msg.payload)

        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message
        client.connect(config.host, config.port)
        client.loop_start()

if __name__ == '__main__':
    config = Config()
    MachinePulpitApp().run()
