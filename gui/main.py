from kivy.app import App
from kivy.uix.stacklayout import StackLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
import paho.mqtt.client as mqtt
from config import Config
import requests
from kivy_garden.graph import Graph, MeshLinePlot
import math

def get_plot_dict(data):
    y_add = math.ceil(math.ceil(data['avg']) * 0.1)
    return dict(
        xlabel=f"Wykres pomiarów na żywo dla urządzenia: {data['device']['model']}", 
        ylabel=data['measurments'][0]['unit'],
        x_ticks_major=25, 
        y_ticks_major=y_add, 
        y_grid_label=True, 
        x_grid_label=True, 
        padding=5, 
        x_grid=True,
        y_grid=True, 
        ymin=math.ceil(data['min']) - y_add, 
        ymax=math.ceil(data['max']) + y_add, 
        xmin=0, 
        xmax=50
    )
        
class DeviceInfoController:
    """Changes info about device on the screen, 
    sets mode and sends it to the server"""
    _device_rows = {}
    _device_detail = []
    _values = []
    _plot_topic = None
    _plot_device_info = None

    @classmethod
    def get_device_topic(cls):
        return cls._device_detail[7]

    @classmethod
    def add_device(cls, key, mode, value, unit):
        cls._device_rows[key] = (mode, value, unit)

    @classmethod
    def update_row_info(cls, key, value, unit):
        if unit in ['CELCIUS', 'FAHRENHEIT', 'KELVIN']:
            cls._device_rows[key][1].text = value[:7]
            cls._device_rows[key][2].text = unit
        else:
            cls._device_rows[key][1].text = value
            cls._device_rows[key][2].text = unit

    @classmethod
    def change_mode(cls, instance):
        instance.current_mode += 1
        if instance.current_mode == 3:
            instance.current_mode = 0
        request = config.change_mode.format(instance.topic_short, instance.current_mode)
        requests.post(request)
        cls._device_rows[instance.topic][0].text = f'Tryb: {instance.current_mode}'

    @classmethod
    def change_screen_to_device_details(cls, instance):
        app = App.get_running_app()
        request = config.show_device_measurements.format(instance.short_topic)
        response = requests.get(request).json()
        cls._device_detail[7] = instance.topic
        cls._device_detail[0].text = f"[b]ID: {instance.short_topic}\nTyp: {response['device']['type']}\nModel: {instance.model}[/b]"
        cls._device_detail[1].text = '\n'.join([f"{measurement['datetime']} - {measurement['value']} {measurement['unit']}" for measurement in response['measurments']])
        cls._device_detail[2].text = '\n'.join([f"{measurement['datetime']} - {measurement['value']} {measurement['unit']}" for measurement in response['modes']])
        if response['device']['type'] in ['Thermometer']:
            cls._device_detail[3].text = f"Średnia wartość\n{str(response['avg'])[:6]}"
            cls._device_detail[4].text = f"Maksymalna wartość\n{str(response['max'])[:6]}"
            cls._device_detail[5].text = f"Minimalna wartość\n{str(response['min'])[:6]}"
        else:
            cls._device_detail[3].text = f"Średnia wartość\n{response['avg']}"
            cls._device_detail[4].text = f"Maksymalna wartość\n{response['max']}"
            cls._device_detail[5].text = f"Minimalna wartość\n{response['min']}"
        cls._device_detail[6].text = f"Czas pracy\n{response['worktime']}"
        app.root.transition.direction = "left"
        app.root.current = 'device_details'

    @classmethod
    def set_device_detail_labels(cls, label_detail, label_measurements, label_modes, label_today_avg, 
        label_today_max, label_today_min, label_device_work_time):
        cls._device_detail = [label_detail, label_measurements, label_modes, label_today_avg, 
        label_today_max, label_today_min, label_device_work_time] + [None]

    @classmethod
    def change_screen_to_plot(cls, instance):
        app = App.get_running_app()
        cls._plot_topic = instance.topic
        if instance.type in ['Thermometer']:
            request = config.change_mode.format(instance.short_topic, 0)
            requests.post(request)
        request = config.show_device_measurements.format(instance.short_topic)
        cls._plot_device_info = requests.get(request).json()
        print(cls._plot_device_info)
        app.root.transition.direction = "left"
        app.root.current = 'device_plot'

    @classmethod
    def get_plot_device_info(cls):
        return cls._plot_device_info

    @classmethod
    def is_correct_topic(cls, topic):
        return cls._plot_topic == topic

class DeviceLayoutFactory:
    """Factory for invidual device"""
    @staticmethod
    def create(device) -> Widget:
        layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=50)
        layout.add_widget(Label(text=device['model']))
        label_mode = Label(text=str(f"Tryb: {device['mode']}"))
        label_value = Label(text='0')
        label_unit = Label(text='None')
        DeviceInfoController.add_device(device['topic'], label_mode, label_value, label_unit)
        layout.add_widget(label_mode)
        layout.add_widget(label_value)
        layout.add_widget(label_unit)
        btn_change_mode = Button(text='Zmień tryb')
        btn_change_mode.topic_short = device['topic_short']
        btn_change_mode.topic = device['topic']
        btn_change_mode.current_mode = device['mode']
        btn_change_mode.bind(on_press=DeviceInfoController.change_mode)
        layout.add_widget(btn_change_mode)
        btn_show_details = Button(text='Szczegóły', on_press=DeviceInfoController.change_screen_to_device_details)
        btn_show_details.short_topic = device['topic_short']
        btn_show_details.topic = device['topic']
        btn_show_details.model = device['model']
        layout.add_widget(btn_show_details)
        if device['type'] in ['Alarm', 'Sensor', 'Light']:
            btn_show_plot = Button(text='Wykres wyłączony', disabled=True)
        else:
            btn_show_plot = Button(text='Wykres', on_press=DeviceInfoController.change_screen_to_plot)
            btn_show_plot.topic = device['topic']
            btn_show_plot.type = device['type']
            btn_show_plot.short_topic = device['topic_short']
        layout.add_widget(btn_show_plot)
        return layout

class DevicePlotScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'device_plot'
    
    def on_pre_enter(self, *args):
        """Create plot with params that are correct to data"""
        device_info = DeviceInfoController.get_plot_device_info()
        self.device_plot_layout = DevicePlotLayout(plot_info=get_plot_dict(device_info))
        self.add_widget(self.device_plot_layout)
        return super().on_pre_enter(*args)

    def on_pre_leave(self, *args):
        """Stop plot update, remove widgets"""
        global measurements
        measurements = []
        self.device_plot_layout.on_leave()
        self.clear_widgets()
        return super().on_pre_leave(*args)

class DevicePlotLayout(BoxLayout):
    def __init__(self, plot_info, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.plot = MeshLinePlot(color=[1, 0, 0, 1])
        self.graph = Graph(**plot_info)
        self.add_widget(self.graph)
        button_return = Button(text='Wróć', on_press=self.back, markup=True, background_color=(255, 0, 0, 1))
        button_start = Button(text='Start', on_press=self.start_plotting)
        button_stop = Button(text='Stop', on_press=self.stop_plotting)
        control_buttons_menu = BoxLayout(orientation='horizontal', size_hint=(1, None), height=50)
        control_buttons_menu.add_widget(button_return)
        control_buttons_menu.add_widget(button_start)
        control_buttons_menu.add_widget(button_stop)
        self.add_widget(control_buttons_menu)

    @staticmethod
    def back(instance):
        app = App.get_running_app()
        app.root.current = app.last_screen

    def start_plotting(self, instance):
        self.graph.add_plot(self.plot)
        Clock.schedule_interval(self.get_value, 0.001)

    def on_leave(self):
        Clock.unschedule(self.get_value)

    def stop_plotting(self, instance):
        Clock.unschedule(self.get_value)

    def get_value(self, dt):
        self.plot.points = [(i, j) for i, j in enumerate(measurements)]

class MyLabel(Label):
   def on_size(self, *args):
      self.text_size = self.size

class DeviceDetailsScreen(Screen):
    """Screen with details about device"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        box_main = BoxLayout(orientation='vertical')
        box_main.add_widget(Button(text='Wróć do tematu', on_press=self.back, size_hint=(0.16, None), height=50, font_size='20sp', 
            markup=True, background_color=(255, 0, 0, 1)))
        label_device = Label(text='', font_size='20sp', markup=True, size_hint=(1, 0.3))
        label_measurements = Label(text='', font_size='13sp', padding=(5,5))
        box_main.add_widget(label_device)
        box_lower = BoxLayout(orientation='horizontal', size_hint=(1, 0.7))
        box_lower_left = BoxLayout(orientation='vertical', size_hint=(0.3, 1))
        box_lower_left.add_widget(Label(text='Ostanie zapisane pomiary', size_hint=(1, None), height=50, font_size='20sp'))
        box_lower_left.add_widget(label_measurements)
        box_lower_mid = BoxLayout(orientation='vertical', size_hint=(0.3, 1))
        box_lower_mid.add_widget(Label(text='Zapisane zmiany trybu', size_hint=(1, None), height=50, font_size='20sp'))
        label_mode = Label(text='.....', font_size='13sp', padding=(5,5))
        box_lower_mid.add_widget(label_mode)
        box_lower_right = BoxLayout(orientation='vertical', size_hint=(0.4, 1))
        box_lower_right.add_widget(Label(text='Dane urządzenia', size_hint=(1, None), height=50, font_size='20sp'))
        labels = [MyLabel(text='Placeholder', size_hint=(0.7, 0.2), pos_hint={'center_x': 0.5}, font_size='17sp', halign="left", valign="middle") for _ in range(4)]
        for label in labels:
            box_lower_right.add_widget(label)
        box_lower.add_widget(box_lower_left)
        box_lower.add_widget(box_lower_mid)
        box_lower.add_widget(box_lower_right)
        box_main.add_widget(box_lower)
        DeviceInfoController.set_device_detail_labels(label_device, label_measurements, label_mode, *labels)
        self.add_widget(box_main)

    def on_leave(self, *args):
        app = App.get_running_app()
        app.root.transition.direction = "right"
        app.last_screen = self.name

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
        self.add_widget(Label(text=f'[b]Temat: {topic}[/b]', font_size='20sp', 
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
            button = Button(text=f'Temat: {topic}', font_size='30sp')
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
                print(device)
                topic_detail.add_widget(DeviceLayoutFactory().create(device))
            topic_detail_screen.add_widget(topic_detail)
            sm.add_widget(topic_detail_screen)
        sm.add_widget(DeviceDetailsScreen(name='device_details'))
        sm.add_widget(DevicePlotScreen())
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
                if self.root.current == 'device_plot' and DeviceInfoController.is_correct_topic(msg.topic):
                    global measurements
                    if len(measurements) >= 50:
                        measurements = []
                    measurements.append(float(msg.payload.split('/')[1]))
                    print('im at device plot')
                    print('class topic', DeviceInfoController._plot_topic)
                    print("[INFO   ] [MQTT        ] topic: " + msg.topic + " msg: " + msg.payload)

        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message
        client.connect(config.host, config.port)
        client.loop_start()

if __name__ == '__main__':
    measurements = []
    config = Config()
    MachinePulpitApp().run()
