import direct.gui.DirectGuiGlobals as DGG
from panda3d.core import Point3, LColor, Vec4
from panda3d.core import TextNode
from panda3d.core import TransparencyAttrib
from direct.gui.DirectGui import DirectEntry, DirectFrame, DirectLabel, DirectButton, DirectRadioButton


class RadioButton(DirectRadioButton):

    def __init__(self, parent, txt, pos, variable, command):
        super().__init__(
            parent=parent,
            pos=pos,
            frameSize=(-2.5, 2.5, -0.5, 0.5),
            frameColor=(1, 1, 1, 0),
            scale=0.06,
            text_align=TextNode.ALeft,
            text=txt,
            text_pos=(-1.5, -0.3),
            text_fg=(1, 1, 1, 1),
            value=[txt],
            variable=variable,
            command=command
        )
        self.initialiseoptions(type(self))


class Button(DirectButton):

    def __init__(self, parent, txt, pos, command):
        super().__init__(
            parent=parent,
            pos=pos,
            relief=DGG.RAISED,
            frameSize=(-0.255, 0.255, -0.05, 0.05),
            frameColor=Gui.frame_color,
            borderWidth=(0.01, 0.01),
            text=txt,
            text_fg=Gui.text_color,
            text_scale=Gui.text_size,
            # text_font=self.font,
            text_pos=(0, -0.01),
            command=command
        )
        self.initialiseoptions(type(self))

    def make_deactivate(self):
        self['state'] = DGG.DISABLED

    def make_activate(self):
        self['state'] = DGG.NORMAL


class Label(DirectLabel):

    def __init__(self, parent, txt, pos):
        super().__init__(
            parent=parent,
            pos=pos,
            frameColor=LColor(1, 1, 1, 0),
            text=txt,
            text_fg=Gui.text_color,
            # text_font=self.font,
            text_scale=Gui.text_size,
            text_align=TextNode.ALeft
        )
        self.initialiseoptions(type(self))


class Entry(DirectEntry):

    def __init__(self, parent, pos, txt='', width=4):
        super().__init__(
            parent=parent,
            pos=pos,
            relief=DGG.SUNKEN,
            frameColor=Gui.frame_color,
            text_fg=Gui.text_color,
            width=width,
            scale=Gui.text_size,
            numLines=1,
            # text_font=self.font,
            initialText=txt,
        )
        self.initialiseoptions(type(self))

    def change_frame_color(self, warning=False):
        if warning:
            self['frameColor'] = LColor(1, 0, 0, 0.3)
        else:
            if self['frameColor'] != Gui.frame_color:
                self['frameColor'] = Gui.frame_color


class Gui(DirectFrame):

    frame_color = LColor(0.6, 0.6, 0.6, 1)
    text_color = LColor(1.0, 1.0, 1.0, 1.0)
    text_size = 0.06

    def __init__(self, parent):
        super().__init__(
            parent=parent,
            frameSize=Vec4(-0.6, 0.6, -1., 1.),
            frameColor=Gui.frame_color,
            pos=Point3(0, 0, 0),
            relief=DGG.SUNKEN,
            borderWidth=(0.01, 0.01)
        )
        self.initialiseoptions(type(self))
        self.set_transparency(TransparencyAttrib.MAlpha)

        self.default_theme = None
        self.entries = {}
        self.input_items = {
            'scale': float, 'segs_c': int, 'radius': float, 'max_depth': int, 'octaves': int}

    def create_control_widgets(self):
        self.create_entries(0.15)
        self.create_radios(0.85)
        self.create_buttons(-0.7)

    def create_buttons(self, start_z):
        self.relfect_btn = Button(
            self, 'Reflect Changes', Point3(0, 0, start_z), base.start_terrain_change)
        self.output_btn = Button(
            self, 'Output BamFile', Point3(0, 0, start_z - 0.1), '')

    def create_entries(self, start_z):
        """Create entry boxes and their labels.
        """
        for i, name in enumerate(self.input_items.keys()):
            z = start_z - i * 0.1
            Label(self, name, Point3(-0.32, 0.0, z))
            entry = Entry(self, Point3(0.07, 0, z))
            self.entries[name] = entry

            if i == 0:
                entry['focus'] = 1

    def create_radios(self, start_z):
        """Create radio buttons to select a noise and a theme.
        """
        noises = ['SimplexNoise', 'CelullarNoise', 'PerlinNoise']
        themes = ['Mountain', 'SnowMountain', 'Desert']
        self.noise = noises[:1]
        self.theme = themes[:1]

        items = [
            [noises, self.noise, base.create_terrain_generator],
            [themes, self.theme, ''],
        ]

        for names, variable, func in items:
            radios = []

            for i, name in enumerate(names):
                z = start_z - i * 0.08
                pos = (-0.18, 0, z)
                radio = RadioButton(self, name, pos, variable, func)
                radios.append(radio)

                if name == 'Mountain':
                    self.default_theme = radio

            for r in radios:
                r.setOthers(radios)

            start_z = z - 0.08 * 2

    def set_input_values(self, default_values):
        if self.default_theme is not None:
            self.default_theme.check()

        for k, v in default_values.items():
            entry = self.entries[k]
            entry.enterText(str(v))

    def validate_input_values(self):
        invalid_values = 0

        for k, data_type in self.input_items.items():
            entry = self.entries[k]

            try:
                data_type(entry.get())
            except ValueError:
                entry.change_frame_color(warning=True)
                invalid_values += 1
            else:
                entry.change_frame_color()

        if invalid_values == 0:
            return True

    def get_input_values(self):
        input_values = {}

        for k, data_type in self.input_items.items():
            v = data_type(self.entries[k].get())
            input_values[k] = v

        return input_values

    def get_checked_noise(self):
        return self.noise[0]

    def get_checked_theme(self):
        return self.theme[0]

    def disable_buttons(self):
        self.relfect_btn.make_deactivate()
        self.output_btn.make_deactivate()

    def enable_buttons(self):
        self.relfect_btn.make_activate()
        self.output_btn.make_activate()