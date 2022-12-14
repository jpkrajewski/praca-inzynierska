# Praca inżynierska

Temat pracy dyplomowej: Wykorzystanie protokołu MQTT i platformy Kivy do tworzenia
aplikacji Internetu Rzeczy

Temat pracy w j. ang.: Design of Internet of Things applications with use of the MQTT
protocol and the Kivy platform

#

**Rodzaj pracy: Eksperymantalny; Programowanie**

Zakres pracy:
1. Technologie i narzędzia niezbędne do tworzenia aplikacji w języku Python.
Protokół MQTT i jego wykorzystanie w aplikacjach Internetu Rzeczy. Wybrana
biblioteka MQTT dla języka Python i jej możliwości. Platforma Kivy i jej wykorzystanie
w aplikacjach z graficznym interfejsem użytkownika. Przegląd wbudowanych
funkcjonalności Kivy, dostępnych komponentów GUI i sposobu obsługi zdarzeń.

2. Implementacja przykładowej aplikacji z wykorzystaniem języka Python, platformy Kivy
oraz wybranej biblioteki MQTT, demonstrującej możliwości wykorzystanych platform.

3. Opis zrealizowanej części praktycznej, a w tym założeń projektowych i ważniejszych
aspektów implementacji. Opis funkcjonalności opracowanej aplikacji

#

## Architektura systemu

![](https://raw.githubusercontent.com/jpkrajewski/praca-inzynierska/main/docs/projekt.png)

## Symulowane urządzenia
Stworzyłem kilka rodzajów urządzeń. Wszystkie urządzenia dziedziczą od bazowej klasy BaseDevice i za pomocą kompozycji z generatorem wartości tworzą konkretne urządzenia. Wartości generowane są losowo zgodnie z podanym zakresem oraz typem jaki mają zwracać.
<br>
![](https://raw.githubusercontent.com/jpkrajewski/praca-inzynierska/main/docs/uml%20device.png)
#
* **Termometr** - Urządzenie to wysyła temperaturę temperatury z zakresu 30 - 35 stopni, ma trzy tryby:
    1. wysyła temperaturę w skali Celcjusza, 
    2. wysyła temperaturę w skali Fahrenheita, 
    3. wysyła temperaturę w skali Kelvina.
```python
    >>> print(message.payload.decode('utf-8')) 
    >>> "CELCIUS/36.5"
```
* **Sensor** - Urządzenie to wysyła informacje o tym czy coś zostało wykryte, na przykład czy materiał jest w dobrym miejscu na taśmie i można go ciąć, czyli włączyć piłę.
```python
    >>> print(message.payload.decode('utf-8')) 
    >>> "DETECTED/NO"
```
* **Piła** - Urządzenie to wysyła aktualną ilość obrotów w zakresie 0 lub 7000
```python
    >>> print(message.payload.decode('utf-8')) 
    >>> "RPM/7000"
```
* **Wiatrak** - Urządzenie to symuluje obroty zakresie ~2000 - 10000 i je wysyła w zależności od trybu pracy:
    1. symuluje obroty w zakresie ~2000 
    2. symuluje obroty w zakresie ~6000 
    3. symuluje obroty w zakresie ~10000
```python
    >>> print(message.payload.decode('utf-8')) 
    >>> "RPM/9372"
```
* **LED** - Urządzenie to symuluje działanie diody LED, wysyła informacje o tym jaki tryb jest włączony:

    1. dioda LED świeci na zielono
    2. dioda LED świetci na czerwono
    3. dioda LED świeci na niebiesko
```python
    >>> print(message.payload.decode('utf-8')) 
    >>> "LUMEN/700-RED"
```
* **Alarm** - Urządzenie to symuluje działanie alarmu, wysyła informacje o tym jaki tryb jest włączony:
    1. Alarm cichy
    2. Alarm głośny
```python
    >>> print(message.payload.decode('utf-8')) 
    >>> "LOUD/OFF"
```
## Server Flask API
Aplikacja Flask postawiona na serverze AWS, instancja EC2, Linux ubuntu.
### Funkcjonalność
* Odbiera wiadomości od urządzeń i zapisuje je do bazy danych
* Odbiera wiadomości od aplikacji Kivy (zmiana trybu pracy) i wysyła je do urządzeń
* Wysyła wyszystkie potrzebne dane konfiguracyjne do aplikacji Kivy oraz symulowanych urządzeń

### Endpointy
Wszystkie endpoint udokumentowałem w Postman Doc, który znajduje się pod tym linkiem:
<br>
https://documenter.getpostman.com/view/13647202/2s83zjsPPH

## Kivy Graficzny interfejs użytkownika
Aplikacja posiada 3 widoki:
* Widok główny - wyświetla wszystkie dostępne tematy MQTT
* Widok tematu - wyświetla wszystkie wiadomości z danego tematu, oraz umożliwia wysyłanie wiadomości do urządzeń, w tym przypadku zmiana trybu pracy
* Widok urządzenia - wyświetla wszystkie wiadomości z danego urządzenia, z datami. Date zmiany trybu, jeśli urządzenia wysyła dane policzalne (np. temperatura, obroty) widok ten wyświetla średnia z dnia, maksymalną i minimalną wartość z dnia. Ponadto wyświetla czas pracy urządzenia.

### Widok główny
![](https://raw.githubusercontent.com/jpkrajewski/praca-inzynierska/main/docs/gui_menu.png)

### Widok tematu
![](https://raw.githubusercontent.com/jpkrajewski/praca-inzynierska/main/docs/gui_topic.png)

### Widok urządzenia
![](https://raw.githubusercontent.com/jpkrajewski/praca-inzynierska/main/docs/gui_device.png)

