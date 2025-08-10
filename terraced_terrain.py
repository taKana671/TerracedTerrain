import sys
import math
from enum import Enum, auto
from datetime import datetime

from direct.gui.DirectWaitBar import DirectWaitBar
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from direct.stdpy import threading
from panda3d.core import Vec3, Vec2, Point3, LColor, Vec4
from panda3d.core import AmbientLight, DirectionalLight
from panda3d.core import NodePath
from panda3d.core import load_prc_file_data
from panda3d.core import OrthographicLens, Camera, MouseWatcher, PGTop
from panda3d.core import AntialiasAttrib


from gui import Gui
from terraced_terrain_generator import TerracedTerrainGenerator
from themes import themes

# Without 'framebuffer-multisample' and 'multisamples' settings,
# there appears to be no effect of 'set_antialias(AntialiasAttrib.MAuto)'.
load_prc_file_data("", """
    win-size 1200 600
    window-title TerracedTerrain
    framebuffer-multisample 1
    multisamples 2
    """)


class Status(Enum):

    DISPLAYING = auto()
    REMOVE = auto()
    CREATE = auto()
    SETUP = auto()
    WAIT = auto()
    FINISH = auto()


class Progress(DirectWaitBar):

    def __init__(self, parent=None):
        self.range_max = 50
        self.bar_color = (1, 1, 1, 1)

        super().__init__(
            parent=parent,
            text='generating...',
            text_fg=self.bar_color,
            text_scale=0.05,
            text_pos=(0, 0.05, 0),
            range=self.range_max,
            value=0,
            barColor=self.bar_color,
            frameSize=(-0.3, 0.3, 0, 0.025),
            pos=(0.3, 0.5, 0.0)
        )
        self.initialiseoptions(type(self))
        self.updateBarStyle()

    def update_progress(self):
        if self['value'] > self.range_max:
            self['value'] -= self.range_max
        else:
            self['value'] += 1

    def finish(self):
        if self['value'] > self.range_max:
            return True
        self['value'] += 1


class TerracedTerrain(ShowBase):

    def __init__(self):
        super().__init__()
        self.disable_mouse()
        # self.setBackgroundColor(0.6, 0.6, 0.6)
        self.render.set_antialias(AntialiasAttrib.MAuto)
        self.setup_light()

        # setup camera.
        self.default_hpr = Vec3(-56.9, 0, 2.8) 
        self.camera_root = NodePath('camera_root')
        self.camera_root.reparent_to(self.render)
        self.camera_root.set_hpr(self.default_hpr)

        # create model display region.
        self.mw3d_node = self.create_display_region(Vec4(0.2, 1.0, 0.0, 1.0))
        # create gui region.
        self.gui_aspect2d = self.create_gui_region(Vec4(0.0, 0.2, 0.0, 1.0), 'gui')

        # create gui.
        self.gui = Gui(self.gui_aspect2d)
        self.gui.create_control_widgets()
        # show terrain.
        self.create_model()
        self.model.reparent_to(self.render)

        self.show_wireframe = False
        self.dragging = False
        self.before_mouse_pos = None
        self.state = Status.DISPLAYING

        self.accept('d', self.toggle_wireframe)
        self.accept('i', self.print_info)
        self.accept('escape', sys.exit)
        self.accept('mouse1', self.mouse_click)
        self.accept('mouse1-up', self.mouse_release)
        self.taskMgr.add(self.update, 'update')

    def output_bam_file(self):
        model_type = self.model_cls.__name__.lower()
        num = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f'{model_type}_{num}.bam'

        output_model = self.model.copy_to(self.render)
        output_model.set_render_mode_filled()
        output_model.set_hpr(Vec3(0, 0, 0))
        output_model.set_color(LColor(1, 1, 1, 1))
        output_model.flatten_strong()

        # output_mode.clear_color()
        output_model.writeBamFile(filename)
        output_model.remove_node()

    def toggle_wireframe(self):
        if self.show_wireframe:
            self.model.set_render_mode_filled()
        else:
            self.model.set_render_mode_wireframe()

        # self.toggle_wireframe()
        self.show_wireframe = not self.show_wireframe

    def print_info(self):
        print(self.camera_root.get_hpr())

    def calc_aspect_ratio(self, display_region):
        """Args:
            display_region (Vec4): (left, right, bottom, top)
            The range is from 0 to 1.
            0: the left and bottom; 1: the right and top.
        """
        props = self.win.get_properties()
        window_size = props.get_size()

        region_w = display_region.y - display_region.x
        region_h = display_region.w - display_region.z
        display_w = int(window_size.x * region_w)
        display_h = int(window_size.y * region_h)

        gcd = math.gcd(display_w, display_h)
        w = display_w / gcd
        h = display_h / gcd
        aspect_ratio = w / h

        return aspect_ratio

    def calc_scale(self, region_size):
        aspect_ratio = self.get_aspect_ratio()

        w = region_size.y - region_size.x
        h = region_size.w - region_size.z
        new_aspect_ratio = aspect_ratio * w / h

        if aspect_ratio > 1.0:
            s = 1. / h
            return Vec3(s / new_aspect_ratio, 1.0, s)
        else:
            s = 1.0 / w
            return Vec3(s, 1.0, s * new_aspect_ratio)

    def create_mouse_watcher(self, name, display_region):
        mw_node = MouseWatcher(name)
        # Gets MouseAndKeyboard, the parent of base.mouseWatcherNode
        # that passes mouse data into MouseWatchers,
        input_ctrl = self.mouseWatcher.get_parent()
        input_ctrl.attach_new_node(mw_node)
        # Restricts new MouseWatcher to the intended display region.
        mw_node.set_display_region(display_region)
        return mw_node

    def create_display_region(self, region_size):
        """Create the region to display a model.
            Args:
                size (Vec4): Vec4(left, right, bottom, top)
        """
        region = self.win.make_display_region(region_size)

        # create custom camera.
        cam = NodePath(Camera('cam3d'))
        aspect_ratio = self.calc_aspect_ratio(region_size)
        cam.node().get_lens().set_aspect_ratio(aspect_ratio)
        region.set_camera(cam)
        self.camNode.set_active(False)

        cam.set_pos(Point3(30, -30, 0))
        cam.look_at(Point3(0, 0, 0))
        cam.reparent_to(self.camera_root)

        # create a MouseWatcher of the region.
        mw3d_node = self.create_mouse_watcher('mw3d', region)

        return mw3d_node

    def create_gui_region(self, region_size, name):
        """Create the custom 2D region for gui.
            Args:
                size (Vec4): Vec4(left, right, bottom, top)
        """
        region = self.win.make_display_region(region_size)
        region.set_sort(20)
        # region.set_clear_color((0.5, 0.5, 0.5, 1.))
        # region.set_clear_color_active(True)

        # create custom camera.
        cam = NodePath(Camera(f'cam_{name}'))
        lens = OrthographicLens()
        lens.set_film_size(2, 2)
        lens.set_near_far(-1000, 1000)
        cam.node().set_lens(lens)

        gui_render2d = NodePath(f'cam_{name}')
        gui_render2d.set_depth_test(False)
        gui_render2d.set_depth_write(False)

        cam.reparent_to(gui_render2d)
        region.set_camera(cam)

        gui_aspect2d = gui_render2d.attach_new_node(PGTop(f'gui_{name}'))
        scale = self.calc_scale(region_size)
        gui_aspect2d.set_scale(scale)

        # create a MouseWatcher of the region.
        mw2d_nd = self.create_mouse_watcher(f'mw_{name}', region)
        gui_aspect2d.node().set_mouse_watcher(mw2d_nd)

        return gui_aspect2d

    def setup_light(self):
        ambient_light = NodePath(AmbientLight('ambient_light'))
        ambient_light.reparent_to(self.render)
        ambient_light.node().set_color(LColor(0.6, 0.6, 0.6, 1.0))
        self.render.set_light(ambient_light)

        directional_light = NodePath(DirectionalLight('directional_light'))
        directional_light.node().get_lens().set_film_size(200, 200)
        directional_light.node().get_lens().set_near_far(1, 100)

        directional_light.node().set_color(LColor(1, 1, 1, 1))
        directional_light.set_pos_hpr(Point3(0, 20, 50), Vec3(-30, -45, 0))

        # directional_light.node().show_frustum()
        self.render.set_light(directional_light)
        directional_light.node().set_shadow_caster(True)
        self.render.set_shader_auto()

    def mouse_click(self):
        self.dragging = True
        self.dragging_start_time = globalClock.get_frame_time()

    def mouse_release(self):
        self.dragging = False
        self.before_mouse_pos = None

    def rotate_camera(self, mouse_pos, dt):
        if self.before_mouse_pos:
            angle = Vec3()

            if (delta := mouse_pos.x - self.before_mouse_pos.x) < 0:
                angle.x += 180
            elif delta > 0:
                angle.x -= 180

            if (delta := mouse_pos.y - self.before_mouse_pos.y) < 0:
                angle.z -= 180
            elif delta > 0:
                angle.z += 180

            angle *= dt
            self.camera_root.set_hpr(self.camera_root.get_hpr() + angle)

        self.before_mouse_pos = Vec2(mouse_pos.xy)

    def start_terrain_change(self):
        if self.state == Status.DISPLAYING:
            if self.gui.validate_input_values():
                self.state = Status.REMOVE

    def remove_current_terrain(self):
        self.model.remove_node()
        self.model = None

    def create_model(self):
        self.model = self.terrain_generator.create()
        self.model.set_pos_hpr_scale(Point3(0, 0, 0), Vec3(0, 45, 0), 4)

    def change_terrain_attributes(self):
        input_values = self.gui.get_input_values()

        for k, v in input_values.items():
            setattr(self.terrain_generator, k, v)

        theme_name = self.gui.get_checked_theme()
        theme = themes[theme_name.lower()]
        setattr(self.terrain_generator, "theme", theme)

    def create_terrain_generator(self):
        noise = self.gui.get_checked_noise()

        match noise:
            case 'SimplexNoise':
                self.terrain_generator = TerracedTerrainGenerator.from_simplex()

            case 'CelullarNoise':
                self.terrain_generator = TerracedTerrainGenerator.from_cellular()

            case 'PerlinNoise':
                self.terrain_generator = TerracedTerrainGenerator.from_perlin()

        default_values = {k: getattr(self.terrain_generator, k) for k in self.gui.input_items.keys()}
        self.gui.set_input_values(default_values)

    def update(self, task):
        dt = globalClock.get_dt()

        match self.state:

            case Status.DISPLAYING:

                if self.mw3d_node.has_mouse():
                    mouse_pos = self.mw3d_node.get_mouse()

                    if self.dragging:
                        if globalClock.get_frame_time() - self.dragging_start_time >= 0.2:
                            self.rotate_camera(mouse_pos, dt)

            case Status.REMOVE:
                self.gui.disable_buttons()
                self.remove_current_terrain()
                self.state = Status.SETUP

            case Status.SETUP:
                self.change_terrain_attributes()
                self.bar = Progress(self.aspect2d)
                self.terrain_create_thread = threading.Thread(target=self.create_model)
                self.terrain_create_thread.start()
                self.state = Status.CREATE

            case Status.CREATE:
                if not self.terrain_create_thread.is_alive():
                    self.state = Status.WAIT
                else:
                    self.bar.update_progress()

            case Status.WAIT:
                if self.bar.finish():
                    self.bar.destroy()
                    self.state = Status.FINISH

            case Status.FINISH:
                self.model.reparent_to(self.render)
                self.camera_root.set_hpr(self.default_hpr)
                self.gui.enable_buttons()
                self.state = Status.DISPLAYING

        return task.cont


if __name__ == '__main__':
    app = TerracedTerrain()
    app.run()