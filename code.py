# (13) (14) (15) (16) (17) (18) (19) (20) [xx] [xx]
#
# (29) (30) (31) (32) (33) (34) (35) (36) [104][105]
#
# (49) (50) (51) (52) (53) (54) (55) (56) [106][107]
#
#  __   __   __   __   __   __   __   __    [105]
#
#                                           [106]
#  77   78   79   80   81   82   83   84
#                                           [107]
#
#  __   __   __   __   __   __   __   __    [108]
#
# [41] [42] [43] [44] [57] [58] [59] [60]
#
# [73] [74] [75] [76] [89] [90] [91] [92]
#

import sys

from typing import Union, Dict, List, Iterator, Tuple
from PyQt5 import QtCore, QtWidgets, QtMultimedia
from collections import OrderedDict
import rtmidi
import rtmidi.midiutil
from enum import IntEnum, unique
import itertools

class Variant(QtCore.QObject):

    changed = QtCore.pyqtSignal(int)

    def __init__(self, value: Union[int, 'Variant'] = 0) -> None:
        super().__init__()
        self.__value: int = value

    def assign(self, value: Union[int, 'Variant']) -> 'Variant':
        self.__value = value
        self.changed.emit(self.__value)
        return self

class Button(QtCore.QObject):

    pressed = QtCore.pyqtSignal()
    hold = QtCore.pyqtSignal()
    released = QtCore.pyqtSignal()
    __start_timer = QtCore.pyqtSignal()
    __stop_timer = QtCore.pyqtSignal()

    def __init__(self, parent = None) -> None:
        super().__init__(parent=parent)
        self.__timer = QtCore.QTimer()
        self.__timer.timeout.connect(self.hold.emit)
        self.__start_timer.connect(self.start_timer)
        self.__stop_timer.connect(self.stop_timer)

    def assign(self, value: Union[int, 'Button']) -> 'Button':
        if type(self).means_pressed(value):
            self.pressed.emit()
            self.__start_timer.emit()
        if type(self).means_released(value):
            self.released.emit()
            self.__stop_timer.emit()
        return self

    def start_timer(self):
        self.__timer.start(1000)

    def stop_timer(self):
        self.__timer.stop()

    @staticmethod
    def means_pressed(value: int) -> bool:
        return value == 127

    @staticmethod
    def means_released(value: int) -> bool:
        return value == 0

class LEDComponent:

    def __init__(self, nova_station: 'NovaStation', index: int):
        self.__nova_station = nova_station
        self.__index = index
        self.__color = NovaStation.Colors.Off
        
    @property
    def index(self) -> int:
        return self.__index

    @property
    def color(self) -> 'NovaStation.Colors':
        return self.__color

    @color.setter
    def color(self, color: 'NovaStation.Colors') -> None:
        self.__color = color
        self.__nova_station.send_message([self.index, color])

    def pulse(self, color: 'NovaStation.Colors') -> None:
        self.__color = NovaStation.Colors.Off
        self.__nova_station.send_message([self.index, color - 4])

class NovaStation:

    class Button(Button):

        def __init__(self, nova_station: 'NovaStation', index: int):
            super().__init__()
            self.__led_component = LEDComponent(nova_station=nova_station, index=index)

        @property
        def led(self):
            return self.__led_component

    class Potentiometer(Variant):

        def __init__(self, nova_station: 'NovaStation', index: int):
            super().__init__()
            self.__led_component = LEDComponent(nova_station=nova_station, index=index)

        @property
        def led(self):
            return self.__led_component

    # class Button(Button):
    # 
    #     def __init__(self, nova_station: 'NovaStation', index: int):
    #         super().__init__()
    #         self.__nova_station = nova_station
    #         self.__index = index
    #         self.__color = NovaStation.Colors.Off
    #         self.__pulse_timer = QtCore.QTimer(self)
    #         self.__pulse_timer.timeout.connect(lambda: self.__set_color(NovaStation.Colors.Off))
    #         self.__pulse_timer.setSingleShot(True)
    #   
    #     @property
    #     def color(self):
    #         return self.__color
    # 
    #     @color.setter
    #     def color(self, color: 'NovaStation.Colors') -> None:
    #         self.__set_color(color)
    # 
    #     def __set_color(self, color: 'NovaStation.Colors') -> None:
    #         self.__color = color
    #         self.__nova_station.send_message([self.__index, color])
    # 
    #     def pulse(self, color: 'NovaStation.Colors') -> None:
    #         self.color = color
    #         self.__pulse_timer.start(200)

    PotentiometerMap = {
        # A       # B       # C      
        13: 'A1', 29: 'B1', 49: 'C1',
        14: 'A2', 30: 'B2', 50: 'C2',
        15: 'A3', 31: 'B3', 51: 'C3',
        16: 'A4', 32: 'B4', 52: 'C4',
        17: 'A5', 33: 'B5', 53: 'C5',
        18: 'A6', 34: 'B6', 54: 'C6',
        19: 'A7', 35: 'B7', 55: 'C7',
        20: 'A8', 36: 'B8', 56: 'C8',
    }

    PotentiometerLEDMap = {
        'A1': 13, 'B1': 14, 'C1': 15,
        'A2': 29, 'B2': 30, 'C2': 31,
        'A3': 45, 'B3': 46, 'C3': 47,
        'A4': 61, 'B4': 62, 'C4': 63,
        'A5': 77, 'B5': 78, 'C5': 79,
        'A6': 93, 'B6': 94, 'C6': 95,
        'A7': 109, 'B7': 110, 'C7': 111,
        'A8': 125, 'B8': 126, 'C8': 127,
    }

    SlidersMap = {
        # Sliders
        77: 'S1',
        78: 'S2',
        79: 'S3',
        80: 'S4',
        81: 'S5',
        82: 'S6',
        83: 'S7',
        84: 'S8',
    }

    ButtonMap = {
        # D.      # E.
        41: 'D1', 73: 'E1',
        42: 'D2', 74: 'E2',
        43: 'D3', 75: 'E3',
        44: 'D4', 76: 'E4',
        57: 'D5', 89: 'E5',
        58: 'D6', 90: 'E6',
        59: 'D7', 91: 'E7',
        60: 'D8', 92: 'E8',
    }

    Name = "Launch Control XL"

    @unique
    class Colors(IntEnum):
        Off = 12
        Red = 15
        Amber = 63
        Yellow = 62
        Green = 60

    def turnoff(self):
        for key in range(256):
            self.opt.send_message([144 + 0, key, 12])

    def rainbow(self):
        index = 0
        while True:
            self.__rainbow(index)
            index += 1
            yield index

    def __rainbow(self, offset = 0):
        Map = type(self).PotentiometerLEDMap
        for index, (green, red) in enumerate(itertools.product([0, 1, 2, 3], [0, 1, 2, 3])):
            key_index = (index + offset) % len(Map)
            key = sorted(Map.keys())[key_index]
            # print(key_index, key, red, green)
            self.opt.send_message([144 + 0, key, green * 16 + red + 12])
   
    def __init__(self) -> None:
        self.__open_device()
        self.ipt.set_callback(self.read)
        self.turnoff()
        self.__inputs: Dict[str, Union[Variant, Button]] = {}
        self.__inputs.update({value: NovaStation.Potentiometer(self, NovaStation.PotentiometerLEDMap[value]) for value in NovaStation.PotentiometerMap.values()})
        self.__inputs.update({value: Variant(0) for value in NovaStation.SlidersMap.values()})
        self.__inputs.update({value: NovaStation.Button(self, key) for key, value in NovaStation.ButtonMap.items()})

    def send_message(self, values: List[int]) -> None:
        self.opt.send_message([144] + values)

    def __find_port(self) -> int:
        # type: List[str]
        midi_ports = self.ipt.get_ports()

        def check_for_current_device(port_description: str) -> bool:
            return port_description.startswith(type(self).Name)
        
        device = next(filter(check_for_current_device, midi_ports), None)
        if device is None:
            return -1
            
        return int(device.split(' ')[-1])

    def __open_device(self) -> rtmidi.MidiIn:
        # self.ipt = rtmidi.MidiIn()
        # self.ipt.open_port(self.__find_port())
        self.ipt = rtmidi.midiutil.open_midiinput(port=type(self).Name)[0]
        self.opt = rtmidi.midiutil.open_midioutput(port=type(self).Name)[0]
        
    @property
    def port(self) -> int:
        return 0

    def color_button(self, button: str, color):
        pass

    @staticmethod
    def key_from_message_number(index: int) -> str:
        for Map in [NovaStation.PotentiometerMap, NovaStation.SlidersMap, NovaStation.ButtonMap]:
            if index in Map.keys():
                return Map[index]
        return ''

    def read(self, message: Tuple[Tuple[int, int, int], float], data) -> None:
        # print(message, data)
        key = type(self).key_from_message_number(message[0][1])
        if key:
            self.__inputs[key].assign(int(message[0][2]))

    def input(self, identifier: str):
        return self.__inputs.get(identifier)

    def column(self, index: int):
        return [self.input(k + str(index)) for k in ['A', 'B', 'C', 'S', 'D', 'E']]

class NovaStationWidget(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.__ns = NovaStation()
        self.setStyleSheet("""QLineEdit { color: red };""")
        self.__load_ui()

    @property
    def station(self) -> NovaStation:
        return self.__ns

    def __potentiometer(self, potentiometer: Variant) -> QtWidgets.QLineEdit:
        widget = QtWidgets.QLineEdit(self)
        widget.source = potentiometer
        widget.setMaxLength(3)
        widget.setAlignment(QtCore.Qt.AlignCenter)
        potentiometer.changed.connect(lambda v: widget.setText(str(v)))
        return widget

    def __slider(self, slider: Variant) -> QtWidgets.QSlider:
        widget = QtWidgets.QSlider(QtCore.Qt.Vertical, self)
        widget.source = slider
        widget.setMinimum(0)
        widget.setMaximum(127)
        slider.changed.connect(lambda v: widget.setValue(v))
        return widget

    def __button(self, button: Button) -> QtWidgets.QCheckBox:
        widget = QtWidgets.QCheckBox(self)
        widget.source = button
        button.released.connect(widget.nextCheckState)
        return widget

    def __list_widgets(self) -> Iterator[QtWidgets.QWidget]:
        yield from [self.main_layout.itemAt(i).widget() for i in range(self.main_layout.count())]

    def __change_enability(self, status: bool) -> None:
        for widget in self.__list_widgets():
            widget.setEnabled(status)

    def enable(self) -> None:
        self.__change_enability(True)

    def disable(self) -> None:
        self.__change_enability(False)

    def __load_ui(self) -> None:
        self.A1 = self.__potentiometer(self.__ns.input('A1'))
        self.A2 = self.__potentiometer(self.__ns.input('A2'))
        self.A3 = self.__potentiometer(self.__ns.input('A3'))
        self.A4 = self.__potentiometer(self.__ns.input('A4'))
        self.A5 = self.__potentiometer(self.__ns.input('A5'))
        self.A6 = self.__potentiometer(self.__ns.input('A6'))
        self.A7 = self.__potentiometer(self.__ns.input('A7'))
        self.A8 = self.__potentiometer(self.__ns.input('A8'))
                                                          
        self.B1 = self.__potentiometer(self.__ns.input('B1'))
        self.B2 = self.__potentiometer(self.__ns.input('B2'))
        self.B3 = self.__potentiometer(self.__ns.input('B3'))
        self.B4 = self.__potentiometer(self.__ns.input('B4'))
        self.B5 = self.__potentiometer(self.__ns.input('B5'))
        self.B6 = self.__potentiometer(self.__ns.input('B6'))
        self.B7 = self.__potentiometer(self.__ns.input('B7'))
        self.B8 = self.__potentiometer(self.__ns.input('B8'))
                                                             
        self.C1 = self.__potentiometer(self.__ns.input('C1'))
        self.C2 = self.__potentiometer(self.__ns.input('C2'))
        self.C3 = self.__potentiometer(self.__ns.input('C3'))
        self.C4 = self.__potentiometer(self.__ns.input('C4'))
        self.C5 = self.__potentiometer(self.__ns.input('C5'))
        self.C6 = self.__potentiometer(self.__ns.input('C6'))
        self.C7 = self.__potentiometer(self.__ns.input('C7'))
        self.C8 = self.__potentiometer(self.__ns.input('C8'))
                                                            
        self.S1 = self.__slider(self.__ns.input('S1')) 
        self.S2 = self.__slider(self.__ns.input('S2')) 
        self.S3 = self.__slider(self.__ns.input('S3')) 
        self.S4 = self.__slider(self.__ns.input('S4')) 
        self.S5 = self.__slider(self.__ns.input('S5')) 
        self.S6 = self.__slider(self.__ns.input('S6')) 
        self.S7 = self.__slider(self.__ns.input('S7')) 
        self.S8 = self.__slider(self.__ns.input('S8')) 
                                                      
        self.D1 = self.__button(self.__ns.input('D1'))
        self.D2 = self.__button(self.__ns.input('D2'))
        self.D3 = self.__button(self.__ns.input('D3'))
        self.D4 = self.__button(self.__ns.input('D4'))
        self.D5 = self.__button(self.__ns.input('D5'))
        self.D6 = self.__button(self.__ns.input('D6'))
        self.D7 = self.__button(self.__ns.input('D7'))
        self.D8 = self.__button(self.__ns.input('D8'))
                                                      
        self.E1 = self.__button(self.__ns.input('E1'))
        self.E2 = self.__button(self.__ns.input('E2'))
        self.E3 = self.__button(self.__ns.input('E3'))
        self.E4 = self.__button(self.__ns.input('E4'))
        self.E5 = self.__button(self.__ns.input('E5'))
        self.E6 = self.__button(self.__ns.input('E6'))
        self.E7 = self.__button(self.__ns.input('E7'))
        self.E8 = self.__button(self.__ns.input('E8'))

        self.main_layout = QtWidgets.QGridLayout()
        def add_widget_to_main_layout(widget, row, column):
          self.main_layout.addWidget(widget, row, column, QtCore.Qt.AlignCenter)

        add_widget_to_main_layout(self.A1, 0, 0)
        add_widget_to_main_layout(self.A2, 0, 1)
        add_widget_to_main_layout(self.A3, 0, 2)
        add_widget_to_main_layout(self.A4, 0, 3)
        add_widget_to_main_layout(self.A5, 0, 4)
        add_widget_to_main_layout(self.A6, 0, 5)
        add_widget_to_main_layout(self.A7, 0, 6)
        add_widget_to_main_layout(self.A8, 0, 7)

        add_widget_to_main_layout(self.B1, 1, 0)
        add_widget_to_main_layout(self.B2, 1, 1)
        add_widget_to_main_layout(self.B3, 1, 2)
        add_widget_to_main_layout(self.B4, 1, 3)
        add_widget_to_main_layout(self.B5, 1, 4)
        add_widget_to_main_layout(self.B6, 1, 5)
        add_widget_to_main_layout(self.B7, 1, 6)
        add_widget_to_main_layout(self.B8, 1, 7)

        add_widget_to_main_layout(self.C1, 2, 0)
        add_widget_to_main_layout(self.C2, 2, 1)
        add_widget_to_main_layout(self.C3, 2, 2)
        add_widget_to_main_layout(self.C4, 2, 3)
        add_widget_to_main_layout(self.C5, 2, 4)
        add_widget_to_main_layout(self.C6, 2, 5)
        add_widget_to_main_layout(self.C7, 2, 6)
        add_widget_to_main_layout(self.C8, 2, 7)

        add_widget_to_main_layout(self.S1, 3, 0)
        add_widget_to_main_layout(self.S2, 3, 1)
        add_widget_to_main_layout(self.S3, 3, 2)
        add_widget_to_main_layout(self.S4, 3, 3)
        add_widget_to_main_layout(self.S5, 3, 4)
        add_widget_to_main_layout(self.S6, 3, 5)
        add_widget_to_main_layout(self.S7, 3, 6)
        add_widget_to_main_layout(self.S8, 3, 7)

        add_widget_to_main_layout(self.D1, 4, 0)
        add_widget_to_main_layout(self.D2, 4, 1)
        add_widget_to_main_layout(self.D3, 4, 2)
        add_widget_to_main_layout(self.D4, 4, 3)
        add_widget_to_main_layout(self.D5, 4, 4)
        add_widget_to_main_layout(self.D6, 4, 5)
        add_widget_to_main_layout(self.D7, 4, 6)
        add_widget_to_main_layout(self.D8, 4, 7)

        add_widget_to_main_layout(self.E1, 5, 0)
        add_widget_to_main_layout(self.E2, 5, 1)
        add_widget_to_main_layout(self.E3, 5, 2)
        add_widget_to_main_layout(self.E4, 5, 3)
        add_widget_to_main_layout(self.E5, 5, 4)
        add_widget_to_main_layout(self.E6, 5, 5)
        add_widget_to_main_layout(self.E7, 5, 6)
        add_widget_to_main_layout(self.E8, 5, 7)

        self.setLayout(self.main_layout)

class BPMWidget(QtWidgets.QWidget):

    ticked = QtCore.pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent=parent)
        self.__timer = QtCore.QTimer(self)
        self.__timer.timeout.connect(lambda: self.ticked.emit())

        self.__tick_sound = QtMultimedia.QSoundEffect(self)
        self.__tick_sound.setSource(QtCore.QUrl.fromLocalFile("metronome-tick.wav"))
        self.__tick_sound.setLoopCount(1)
        self.__tick_sound.setVolume(0.5)
        self.ticked.connect(self.__tick_sound.play)
        
        self.__load_ui()

        self.__timer.setInterval(10000000)
        self.bpm = 120.0

    @property
    def tick_sound(self):
        return self.__tick_sound

    def __load_ui(self):
        self.__progress = QtWidgets.QWidget(self)
        self.__value = QtWidgets.QLabel(self)
        #
        self.__10bpm_slow_button = QtWidgets.QPushButton('-10', self)
        self.__1bpm_slow_button = QtWidgets.QPushButton('-1', self)
        self.__half_bpm_slow_button = QtWidgets.QPushButton('-0.5', self)
        # 
        self.__half_bpm_quicken_button = QtWidgets.QPushButton('+0.5', self)
        self.__1bpm_quicken_button = QtWidgets.QPushButton('+1', self)
        self.__10bpm_quicken_button = QtWidgets.QPushButton('+10', self)

        self.__10bpm_slow_button.released.connect(lambda: self.__slow(10.0))
        self.__1bpm_slow_button.released.connect(lambda: self.__slow(1.0))
        self.__half_bpm_slow_button.released.connect(lambda: self.__slow(0.5))

        self.__half_bpm_quicken_button.released.connect(lambda: self.__quicken(0.5))
        self.__1bpm_quicken_button.released.connect(lambda: self.__quicken(1.0))
        self.__10bpm_quicken_button.released.connect(lambda: self.__quicken(10.0))

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.__progress, 0, 0, -1, 1)
        layout.addWidget(self.__10bpm_slow_button, 1, 0)
        layout.addWidget(self.__1bpm_slow_button, 1, 1)
        layout.addWidget(self.__half_bpm_slow_button, 1, 2)
        layout.addWidget(self.__value, 1, 3)
        layout.addWidget(self.__half_bpm_quicken_button, 1, 4)
        layout.addWidget(self.__1bpm_quicken_button, 1, 5)
        layout.addWidget(self.__10bpm_quicken_button, 1, 6)

        self.setLayout(layout)

    def __quicken(self, value: float):
        self.bpm = self.bpm + value

    def __slow(self, value: float):
        self.bpm = self.bpm - value

    @property
    def bpm(self) -> float:
        return self.__bpm

    @bpm.setter
    def bpm(self, value: float) -> None:
        self.__bpm = value
        self.__value.setText(str(self.__bpm))
        remaining_ms = self.__timer.remainingTime()
        interval_ms = self.__timer.interval()
        new_interval = 60000 / self.__bpm
        self.__timer.setInterval(new_interval)
        if (remaining_ms == -1 or (interval_ms - new_interval) < remaining_ms):
            self.__timer.start()

class ChannelWidget(QtWidgets.QWidget):

    about_to_record = QtCore.pyqtSignal()
    recording = QtCore.pyqtSignal()
     
    def __init__(self, index, column, parent=None) -> None:
        super().__init__(parent=parent)
        self.index = index
        self.column = column
        self.__playing = None
        self.__output_file = QtCore.QUrl.fromLocalFile(str(index) + ".wav")
        print(self.__output_file)
        #
        self.__sound = QtMultimedia.QSoundEffect(self)
        self.column[3].changed.connect(lambda v: self.__sound.setVolume(v/127.0))
        self.__sound.setLoopCount(1)
        #
        self.__recorder = QtMultimedia.QAudioRecorder(self)
        self.__recorder.error.connect(lambda err: print(err))
        auto_settings = QtMultimedia.QAudioEncoderSettings()
        auto_settings.setCodec("audio/wav")
        self.__recorder.setEncodingSettings(auto_settings)
        self.__recorder.setOutputLocation(self.__output_file)
        
        # auto_settings.setQuality()
        self.record_button.released.connect(self.start_recording)

    @property
    def ticker(self):
        return self.parent().bpm_widget.ticked

    def start_recording(self):
        self.__sound.stop()
        self.record_button.released.disconnect(self.start_recording)
        def foo():
            for i in range(4):
                self.record_button.led.pulse(NovaStation.Colors.Amber)
                yield
            self.record()
        bip = foo()
        self.__about_to_record = lambda: next(bip, None)
        self.parent().bpm_widget.ticked.connect(self.__about_to_record)

    @property
    def record_button(self):
        return self.column[5]

    def play(self):
        self.__sound.play()
        def wait_for_ticks():
            while True:
                yield from range(4)
                self.__sound.play()
        play = wait_for_ticks()
        self.playing = lambda: next(play)

    def stop(self):
        self.__sound.stop()
        if self.__playing:
            self.ticker.disconnect(self.__playing)
            self.__playing = None

    @property
    def playing(self):
        return self.__playing

    @playing.setter
    def playing(self, callback):
        if self.__playing:
            self.ticker.disconnect(self.__playing)
        self.__playing = callback
        self.ticker.connect(self.__playing)

    def record(self):
        print('recording')
        self.record_button.led.color = NovaStation.Colors.Green
        self.ticker.disconnect(self.__about_to_record)
        # self.record_button.set_color(NovaStation.Colors.Amber)
        self.__recorder.record()
        print(self.__recorder.outputLocation())
        def stop_after_four_ticks():
            yield from range(4)
            self.__recorder.stop()
            self.__sound.setSource(self.__recorder.outputLocation())
            self.play()
            self.record_button.led.color = NovaStation.Colors.Off
            self.record_button.released.connect(self.start_recording)
            self.ticker.disconnect(self.handler)

        stop = stop_after_four_ticks()
        self.handler = lambda: next(stop, None)
        self.ticker.connect(self.handler)

class Castor(QtWidgets.QWidget):

    def __init__(self) -> None:
        super().__init__()
        self.__load_ui()

    def __load_ui(self) -> None:
        self.__ns = NovaStationWidget()
        self.__enable_button = QtWidgets.QPushButton('enable', self)
        self.__enable_button.released.connect(self.__ns.enable)
        self.__disable_button = QtWidgets.QPushButton('disable', self)
        self.__disable_button.released.connect(self.__ns.disable)
        self.__bpm_widget = BPMWidget(self)
        self.__ns.S8.valueChanged.connect(lambda v: self.__bpm_widget.tick_sound.setVolume(v / 127.0))
        self.__recorders = [
            ChannelWidget(0, self.__ns.station.column(1), self),
            ChannelWidget(1, self.__ns.station.column(2), self),
            ChannelWidget(2, self.__ns.station.column(3), self),
            ChannelWidget(3, self.__ns.station.column(4), self),
            ChannelWidget(4, self.__ns.station.column(5), self),
            ChannelWidget(5, self.__ns.station.column(6), self),
            ChannelWidget(6, self.__ns.station.column(7), self)
        ]

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.__ns, 0, 0, 1, 2)

        layout.addWidget(self.__enable_button, 1, 0)
        layout.addWidget(self.__disable_button, 1, 1)

        layout.addWidget(self.__bpm_widget, 2, 0, 1, 2)

        self.setLayout(layout)

    @property
    def bpm_widget(self):
        return self.__bpm_widget

if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)
    main = Castor()
    main.show()
    sys.exit(app.exec_())
