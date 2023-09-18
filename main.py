from kivy.config import Config
Config.set('graphics', 'window_state', 'maximized')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.gridlayout import GridLayout
from kivy.uix.behaviors import DragBehavior
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
import os
import shutil
import csv


def load_sounds():
    if not os.path.isdir('Sounds'):
        os.mkdir('Sounds')
    try:
        with open('Sounds/sounds.csv', newline='') as sounds_file:
            reader = csv.DictReader(sounds_file)
            sounds = [x for x in reader]
    except FileNotFoundError:
        sounds_file = open('Sounds/sounds.csv', 'w')
        sounds_file.close()
        sounds = []
    return sounds

def save_sounds(sounds):
    header = list(sounds[0].keys())
    with open('Sounds/sounds.csv', 'w', newline='') as sounds_file:
        writer = csv.DictWriter(sounds_file, fieldnames=header)
        writer.writeheader()
        for dic in sounds:
            writer.writerow(dic)


class Edit(Screen):

    file_name = StringProperty()
    sound_name = StringProperty()
    loop = BooleanProperty()

    def update(self):
        self.ids.file_name_input.text = self.file_name
        self.ids.sound_name_input.text = self.sound_name
        self.ids.loop_checkbox.active = self.loop

    def save(self):
        home_screen = self.get_root_window().children[0].get_screen('Home')
        if os.path.exists('Sounds/'+self.file_name):
            sound_tile = home_screen.ids.sound_tiles.children[self.sound_tile_index]

            sound_tile.sound_name = self.sound_name
            sound_tile.file_name = self.file_name
            sound_tile.loop = self.loop
            sound_tile.update()

            self.get_root_window().children[0].current = 'Home'

    def delete_sound(self):
        if os.path.exists('Sounds/'+self.file_name):
            home_screen = self.get_root_window().children[0].get_screen('Home')
            home_screen.ids.sound_tiles.remove_widget(home_screen.ids.sound_tiles.children[self.sound_tile_index])
            os.remove('Sounds/'+self.file_name)

            self.get_root_window().children[0].current = 'Home'

class Home(Screen):

    sounds = load_sounds()

    def load_sounds(self):
        for index, sound in enumerate(self.sounds):
            self.load_sound(sound, index)

    def load_sound(self, sound, index):
        widget = Sound_Tile()
        for key in sound.keys():
            setattr(widget, key, sound[key])
        widget.dict_index = index
        widget.volume = float(widget.volume)
        widget.loop = eval(widget.loop)
        widget.load()
        self.ids.sound_tiles.add_widget(widget)

    def save_sounds(self):
        new_sounds = []
        for tile in self.ids.sound_tiles.children:
            new_sound = {}
            for key in self.sounds[0].keys():
                new_sound[key] = getattr(tile, key)
            new_sounds += [new_sound]
        save_sounds(new_sounds)

    def on_drop_file(self, window, file, *args):
        file_path, file_name = os.path.split(file)
        file_name = str(file_name)[2:-1]
        shutil.copyfile(file, 'Sounds/'+file_name)

        sound = {
            'file_name': file_name,
            'sound_name': file_name,
            'loop': 'False',
            'x': '0',
            'y': '0',
            'volume': '1'
        }

        self.load_sound(sound, len(self.sounds))
        self.sounds += [sound]


class Sound_Tile(DragBehavior, GridLayout):

    sound_player = None
    file_name = StringProperty()
    sound_name = StringProperty()
    volume = NumericProperty()
    loop = BooleanProperty()

    def update(self):
        self.ids.sound_name_label.text = self.sound_name
        self.ids.volume_slider.value = self.volume
        if self.sound_player:
            self.sound_player.loop = self.loop

    def load(self):
        self.sound_player = SoundLoader.load('Sounds/'+ self.file_name)
        self.sound_player.loop = self.loop
        self.sound_player.volume = self.volume
        self.ids.volume_slider.volume = self.volume

    def adjust_volume(self, value):
        if self.sound_player:
            self.volume = value
            self.sound_player.volume = value

    def play(self):
        if self.sound_player:
            self.sound_player.stop()
            self.sound_player.play()

    def stop(self):
        if self.sound_player:
            self.sound_player.stop()

    def edit(self):
        manager = self.get_root_window().children[0]
        home_screen = manager.get_screen('Home')
        edit_screen = manager.get_screen('Edit')

        edit_screen.dict_index = self.dict_index
        edit_screen.file_name = self.file_name
        edit_screen.sound_name= self.sound_name
        edit_screen.loop = self.loop
        edit_screen.update()
        edit_screen.sound_tile_index = [
                x.ids.sound_name_label.text for x in home_screen.ids.sound_tiles.children
            ].index(self.sound_name)

        manager.current = 'Edit'


class SFX_Program(ScreenManager):
    def __init__(self, **kwargs):
        super().__init__(transition=FadeTransition(), **kwargs)


class SFXApp(App):

    def build(self):
        self.sfx_program = SFX_Program()
        self.sfx_program.get_screen('Home').load_sounds()
        Window.bind(on_drop_file=self.sfx_program.get_screen('Home').on_drop_file)
        return self.sfx_program

    def on_stop(self):
        self.sfx_program.get_screen('Home').save_sounds()


if __name__ == '__main__':
    app = SFXApp()
    app.run()
