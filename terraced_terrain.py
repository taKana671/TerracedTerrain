import sys
import math
from enum import Enum, auto
from datetime import datetime

import direct.gui.DirectGuiGlobals as DGG
from panda3d.core import Vec3, Vec2, Point3, LColor, Vec4
from panda3d.core import AmbientLight, DirectionalLight
from panda3d.core import NodePath, TextNode
from panda3d.core import load_prc_file_data
from panda3d.core import OrthographicLens, Camera, MouseWatcher, PGTop
from panda3d.core import TransparencyAttrib, AntialiasAttrib
from direct.gui.DirectGui import DirectEntry, DirectFrame, DirectLabel, DirectButton, OkDialog
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock


# from shapes.pentagonal_division import PentagonalDivision
from terraced_terrain_generator import TerracedTerrainGenerator

# Without 'framebuffer-multisample' and 'multisamples' settings,
# there appears to be no effect of 'set_antialias(AntialiasAttrib.MAuto)'.
load_prc_file_data("", """
    win-size 1200 600
    window-title ProceduralShapes
    framebuffer-multisample 1
    multisamples 2
    """)

class Status(Enum):

    SHOW_MODEL = auto()
    REPLACE_MODEL = auto()
    REPLACE_CLASS = auto()


class TerracedTerrain(ShowBase):

    def __init__(self):
        super().__init__()
        self.disable_mouse()
        # self.setBackgroundColor(0.6, 0.6, 0.6)
        self.render.set_antialias(AntialiasAttrib.MAuto)
        self.setup_light()

        self.camera_root = NodePath('camera_root')
        self.camera_root.reparent_to(self.render)
        self.camera_root.set_hpr(Vec3(-56.9, 0, 2.8))
        self.camera.set_pos(Point3(30, -30, 0))
        self.camera.look_at(Point3(0, 0, 0))
        self.camera.reparent_to(self.camera_root)

        self.show_wireframe = False
        self.dragging = False
        self.before_mouse_pos = None
        self.state = Status.SHOW_MODEL

        # Show model.
        self.dispay_model()

        self.accept('d', self.toggle_wireframe)
        self.accept('i', self.print_info)
        self.accept('escape', sys.exit)
        self.accept('mouse1', self.mouse_click)
        self.accept('mouse1-up', self.mouse_release)
        self.taskMgr.add(self.update, 'update')

    def dispay_model(self):

        # maker = TerracedTerrainGenerator.from_cellular()
        maker = TerracedTerrainGenerator.from_simplex()
        # maker = TerracedTerrainGenerator.from_perlin()
        self.model = maker.create()
        self.model.set_pos(Point3(0, 0, 0))

        self.model.set_pos_hpr_scale(Point3(0, 0, 0), Vec3(0, 45, 0), 4)
        # self.model.set_color(LColor(1, 0, 0, 1))
        self.model.reparent_to(self.render)

        # self.model = self.loader.load_model('torus_20241012130437.bam')
        # self.model.reparent_to(self.render)
        # self.model.set_texture(self.loader.load_texture('brick.jpg'))

        if self.show_wireframe:
            self.model.set_render_mode_wireframe()

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

        # directional_light.set_pos_hpr(Point3(0, 20, 50), Vec3(-20, -160, 0))

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

    def update(self, task):
        dt = globalClock.get_dt()

        match self.state:

            case Status.SHOW_MODEL:

                if self.mouseWatcherNode.has_mouse():
                    mouse_pos = self.mouseWatcherNode.get_mouse()

                    if self.dragging:
                        if globalClock.get_frame_time() - self.dragging_start_time >= 0.2:
                            self.rotate_camera(mouse_pos, dt)
        return task.cont


if __name__ == '__main__':
    app = TerracedTerrain()
    app.run()