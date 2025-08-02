import array
import math
import random

import numpy as np
from panda3d.core import Vec3, Point3, Vec2

from .create_geometry import ProceduralGeometry
from panda3d.core import NodePath
from panda3d.core import Geom, GeomNode, GeomTriangles
from panda3d.core import Mat4, Vec3
from panda3d.core import GeomVertexFormat, GeomVertexData, GeomVertexArrayFormat


from noise import SimplexNoise, PerlinNoise, CellularNoise
from .themes import Mountain


class TerracedTerrain(ProceduralGeometry):

    def __init__(self, noise, segs_c=5, radius=4, max_depth=6, octaves=3):
        super().__init__()
        self.center = Point3(0, 0, 0)
        self.segs_c = segs_c
        self.radius = radius
        self.max_depth = max_depth
        self.octaves = octaves
        self.noise = noise

    @classmethod
    def from_simplex(cls, segs_c=8, radius=3, max_depth=6, octaves=3):
        noise = SimplexNoise()
        return cls(noise.snoise2, segs_c, radius, max_depth, octaves)

    @classmethod
    def from_perlin(cls, segs_c=5, radius=3, max_depth=6, octaves=3):
        noise = PerlinNoise()
        return cls(noise.pnoise2, segs_c, radius, max_depth, octaves)

    @classmethod
    def from_cellular(cls, segs_c=5, radius=3, max_depth=6, octaves=3):
        noise = CellularNoise()
        return cls(noise.fdist2, segs_c, radius, max_depth, octaves)

    def get_polygon_vertices(self, theta):
        rad = math.radians(theta)
        x = self.radius * math.cos(rad) + self.center.x
        y = self.radius * math.sin(rad) + self.center.y

        return Point3(x, y, 0)

    def generate_basic_polygon(self):
        deg = 360 / self.segs_c

        for i in range(self.segs_c):
            current_i = i + 1

            if (next_i := current_i + 1) > self.segs_c:
                next_i = 1
            pt1 = self.get_polygon_vertices(deg * current_i)
            pt2 = self.get_polygon_vertices(deg * next_i)

            yield (pt1, pt2)

    def generate_midpoints(self, tri):
        """Generates the midpoints of the three sides of a triangle.
            Args:
                tri (list): contains vertices(Point3) of a triangle.
        """
        for p1, p2 in zip(tri, tri[1:] + tri[:1]):
            yield (p1 + p2) / 2

    def generate_triangles(self, tri, depth=1):
        if depth == self.max_depth:
            yield tri
        else:
            midpoints = [p for p in self.generate_midpoints(tri)]

            for i, vert in enumerate(tri):
                ii = n if (n := i - 1) >= 0 else len(midpoints) - 1
                divided = [vert, midpoints[i], midpoints[ii]]
                yield from self.generate_triangles(divided, depth + 1)

            yield from self.generate_triangles(midpoints, depth + 1)

    def get_height(self, x, y, t, offsets):
        height = 0
        amplitude = 1.0
        frequency = 0.055
        persistence = 0.375  # 0.5
        lacunarity = 2.52  # 2.5
        scale = 5  # cellular: 10,  simplex: 5

        for i in range(self.octaves):
            offset = offsets[i]
            fx = x * frequency + offset.x
            fy = y * frequency + offset.y
            noise = self.noise((fx + t) * scale, (fy + t) * scale)
            height += amplitude * noise
            frequency *= lacunarity
            amplitude *= persistence

        return height

    def generate_hills_and_valleys(self):
        t = random.uniform(0, 1000)
        offsets = [Vec2(random.randint(-1000, 1000),
                        random.randint(-1000, 1000)) for _ in range(self.octaves)]

        for pt1, pt2 in self.generate_basic_polygon():
            for tri in self.generate_triangles([pt1, pt2, self.center]):
                for vert in tri:
                    z = self.get_height(vert.x, vert.y, t, offsets)
                    vert.z = z
                yield tri

    def generate_terraced_terrain(self, vertex_cnt, vdata_values, prim_indices):
        for v1, v2, v3 in self.generate_hills_and_valleys():
            # Each point's heights above "sea level". For a flat terrain,
            # it's just the vertical component of the respective vector.
            h1 = v1.z
            h2 = v2.z
            h3 = v3.z

            li = [int(h_ * 10) for h_ in (h1, h2, h3)]
            h_min = np.floor(min(li))
            h_max = np.floor(max(li))

            for h in np.arange(h_min, h_max + 1, 0.5):
                # indicate triangles above the plane.
                h *= 0.1
                points_above = 0

                if h1 < h:
                    if h2 < h:
                        if h3 >= h:
                            points_above = 1          # v3 is above.
                    else:
                        if h3 < h:
                            points_above = 1          # v2 is above.
                            v1, v2, v3 = v3, v1, v2
                        else:
                            points_above = 2          # v2 and v3 are above.
                            v1, v2, v3 = v2, v3, v1
                else:
                    if h2 < h:
                        if h3 < h:
                            points_above = 1          # v1 is above.
                            v1, v2, v3 = v2, v3, v1
                        else:
                            points_above = 2          # v1 and v3 are above.
                            v1, v2, v3 = v3, v1, v2
                    else:
                        if h3 < h:
                            points_above = 2          # v1 and v2 are above.
                        else:
                            points_above = 3          # all vectors are above.

                h1, h2, h3 = v1.z, v2.z, v3.z
                # for each point of the triangle, we also need its projections
                # to the current plane and the plane below. Just set its vertical component to the plane's height.

                # current plane
                v1_c = Point3(v1.x, v1.y, h)
                v2_c = Point3(v2.x, v2.y, h)
                v3_c = Point3(v3.x, v3.y, h)

                # generate mesh polygons for each of the three cases.
                if points_above == 3:
                    # add one triangle.
                    color = self.coloring_step(v1_c.z)
                    self.create_triangle_vertices([v1_c, v2_c, v3_c], color, vdata_values)
                    prim_indices.extend([vertex_cnt, vertex_cnt + 1, vertex_cnt + 2])
                    vertex_cnt += 3
                    continue

                # the plane below; used to make vertical walls between planes.
                v1_b = Point3(v1.x, v1.y, h - 0.05)
                v2_b = Point3(v2.x, v2.y, h - 0.05)
                v3_b = Point3(v3.x, v3.y, h - 0.05)

                # find locations of new points that are located on the sides of the triangle's projections,
                # by interpolating between vectors based on their heights.
                t1 = (h1 - h) / (h1 - h3)  # interpolation value for v1 and v3
                v1_c_n = self.lerp(v1_c, v3_c, t1)
                v1_b_n = self.lerp(v1_b, v3_b, t1)

                t2 = (h2 - h) / (h2 - h3)  # interpolation value for v2 and v3
                v2_c_n = self.lerp(v2_c, v3_c, t2)
                v2_b_n = self.lerp(v2_b, v3_b, t2)

                if points_above == 2:
                    color = self.coloring_step(v1_c.z)
                    # add roof part of the step
                    quad = [v1_c, v2_c, v2_c_n, v1_c_n]
                    self.create_quad_vertices(quad, color, vdata_values, wall=False)
                    prim_indices.extend([vertex_cnt, vertex_cnt + 1, vertex_cnt + 2])
                    prim_indices.extend([vertex_cnt + 2, vertex_cnt + 3, vertex_cnt])
                    vertex_cnt += 4

                    # add wall part of the step
                    quad = [v1_c_n, v2_c_n, v2_b_n, v1_b_n]
                    self.create_quad_vertices(quad, color, vdata_values, wall=True)
                    prim_indices.extend([vertex_cnt, vertex_cnt + 1, vertex_cnt + 2])
                    prim_indices.extend([vertex_cnt, vertex_cnt + 2, vertex_cnt + 3])
                    vertex_cnt += 4

                elif points_above == 1:
                    color = self.coloring_step(v3_c.z)
                    # add roof part of the step
                    self.create_triangle_vertices([v3_c, v1_c_n, v2_c_n], color, vdata_values)

                    # self.create_triangle_vertices(tri, vdata_values)
                    prim_indices.extend([vertex_cnt, vertex_cnt + 1, vertex_cnt + 2])
                    vertex_cnt += 3

                    # add wall part of the step
                    quad = [v2_c_n, v1_c_n, v1_b_n, v2_b_n]
                    self.create_quad_vertices(quad, color, vdata_values, wall=True)
                    prim_indices.extend([vertex_cnt, vertex_cnt + 1, vertex_cnt + 3])
                    prim_indices.extend([vertex_cnt + 1, vertex_cnt + 2, vertex_cnt + 3])
                    vertex_cnt += 4

        return vertex_cnt

    def create_triangle_vertices(self, tri, color, vdata_values):
        normal = Vec3(0, 0, 1)

        for vert in tri:
            vdata_values.extend(vert)
            vdata_values.extend(color)
            vdata_values.extend(normal)
            u, v = self.calc_uv(vert.x, vert.y)
            vdata_values.extend((u, v))

    def create_quad_vertices(self, quad, color, vdata_values, wall=False):
        normal = Vec3(0, 0, 1)

        for vert in quad:
            if wall:
                normal = Vec3(vert.x, vert.y, 0).normalized()

            vdata_values.extend(vert)
            vdata_values.extend(color)
            vdata_values.extend(normal)
            u, v = self.calc_uv(vert.x, vert.y)
            vdata_values.extend((u, v))

    def calc_uv(self, x, y):
        u = 0.5 + x / self.radius * 0.5
        v = 0.5 + y / self.radius * 0.5
        return u, v

    def lerp(self, start, end, t):
        """Args
            start: start_point
            end: end point
            t: Interpolation rate; between 0.0 and 1.0
        """
        return start + (end - start) * t

    def coloring_step(self, z):
        v = math.floor(z * 100) / 100
        # print(z, v)


        if v <= 0.1:
            return self.colors['LAYER_01']

        if v <= 0.2:
            return self.colors['LAYER_02']

        if v <= 0.3:
            return self.colors['LAYER_03']

        if v <= 0.4:
            return self.colors['LAYER_04']

        if v <= 0.5:
            return self.colors['LAYER_05']

        if v <= 0.6:
            return self.colors['LAYER_06']

        if v <= 0.7:
            return self.colors['LAYER_07']

        if v <= 0.8:
            return self.colors['LAYER_08']

        if v <= 0.9:
            return self.colors['LAYER_09']

        if v <= 1.0:
            return self.colors['LAYER_10']

        if v <= 1.1:
            return self.colors['LAYER_11']

        if v <= 1.2:
            return self.colors['LAYER_12']

        if v <= 1.3:
            return self.colors['LAYER_13']

        if v <= 1.4:
            return self.colors['LAYER_14']



        # if v <= 0.1:
        #     return (0.0, 0.0, 1.0, 1.0)

        # if v <= 0.4:
        #     return (0.11, 0.56, 1.0, 1.0)

        # if v <= 0.5:
        #     return (0.52, 0.80, 0.92, 1.0)
        
        # if v <= 0.6:
        #     return (0.54, 0.27, 0.07, 1.0)


        # if v < 0.7:
        #     return (0.60, 0.80, 0.19, 1.0)
        
        # if v < 0.8:
        #     return (0., 0.50, 0., 1.0)
        
        # return (0.0, 0.39, 0.0, 1.0)

    def get_geom_node(self):
        # self.define_variables()

        # Create an outer cylinder.
        vdata_values = array.array('f', [])
        # prim_indices = array.array('H', [])
        prim_indices = array.array('I', [])
        vertex_cnt = 0

        self.colors = Mountain.to_dict()
        # vertex_cnt = self.create_penta(
        #     vertex_cnt, vdata_values, prim_indices)
        # import pdb; pdb.set_trace()
        # vertex_cnt = self.terraced(vertex_cnt, vdata_values, prim_indices)
        # triangles = [tri for tri in self.create_penta()]
        # vertex_cnt = self.terraced(triangles, 0, vdata_values, prim_indices)
        vertex_cnt = self.generate_terraced_terrain(0, vdata_values, prim_indices)

        # Create the geom node.
        geom_node = self.create_geom_node(
            vertex_cnt, vdata_values, prim_indices, 'terrace')

        return geom_node

    def create_geom_node(self, vertex_count, vdata_values, prim_indices, name='vertex'):
        """Args:
            fmt (GeomVertexFormat): physical layout of the vertex data stored within a Geom.
            name (str): the name of data.
            vertex_count (int): the number of vertices.
            vdata_values (array.array): vertex information.
            prim_indices (array.array): vertex order.
        """
        vdata = GeomVertexData(name, self.fmt, Geom.UHStatic)
        vdata.unclean_set_num_rows(vertex_count)
        vdata_mem = memoryview(vdata.modify_array(0)).cast('B').cast('f')
        vdata_mem[:] = vdata_values

        prim = GeomTriangles(Geom.UHStatic)
        prim.set_index_type(Geom.NT_uint32)

        prim_array = prim.modify_vertices()
        prim_array.unclean_set_num_rows(len(prim_indices))
        
        # prim_mem = memoryview(prim_array).cast('B').cast('H')
        prim_mem = memoryview(prim_array).cast('B').cast('I')
        prim_mem[:] = prim_indices
        geom_node = GeomNode('geomnode')
        geom = Geom(vdata)
        geom.add_primitive(prim)
        geom_node.add_geom(geom)
        return geom_node




