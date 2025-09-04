import array
import math
import random

import numpy as np
from panda3d.core import Vec3, Point3, Vec2

from shapes.create_geometry import ProceduralGeometry
from noise import SimplexNoise, PerlinNoise, CellularNoise
from noise import Fractal2D
from themes import themes, Island

from mask.radial_gradient_generator import RadialGradientMask


class TerracedTerrainGenerator(ProceduralGeometry):
    """A class to generate a terraced terrain.
        Args:
            noise (func): Function that generates noise.
            scale (float): The smaller this value is, the more sparse the noise becomes.
            segs_s (int): The number of vertices in the polygon that forms the ground; minimum is 3.
            radius (float): Length from the center of the polygon forming the ground to each vertex.
            max_depth (int): The number of times that triangles, formed by the center point and each
                             vertex of the polygon that forms the ground, are further divided into triangles.
            octaves (int): The number of loops to calculate the height of the vertex coordinates.
            theme (str): one of "mountain", "snowmountain" and "desert".
    """

    def __init__(self, noise, scale=10, segs_c=5, radius=4,
                 max_depth=6, octaves=6, theme='mountain'):
        super().__init__()
        self.center = Point3(0, 0, 0)
        self.noise = noise
        self.scale = scale
        self.segs_c = segs_c
        self.radius = radius
        self.max_depth = max_depth
        self.octaves = octaves
        self.theme = themes.get(theme.lower())

    @classmethod
    def from_simplex(cls, scale=8, segs_c=5, radius=3,
                     max_depth=6, octaves=3, theme='mountain'):
        noise = SimplexNoise()
        return cls(noise.snoise2, scale, segs_c, radius, max_depth, octaves, theme)

    @classmethod
    def from_perlin(cls, scale=15, segs_c=5, radius=3,
                    max_depth=6, octaves=3, theme='mountain'):
        noise = PerlinNoise()
        return cls(noise.pnoise2, scale, segs_c, radius, max_depth, octaves, theme)

    @classmethod
    def from_cellular(cls, scale=10, segs_c=5, radius=3,
                      max_depth=6, octaves=3, theme='mountain'):
        noise = CellularNoise()
        return cls(noise.fdist2, scale, segs_c, radius, max_depth, octaves, theme)

    @classmethod
    def from_fractal(cls, scale=15, segs_c=5, radius=3,
                     max_depth=6, octaves=3, theme='island'):
        simplex = SimplexNoise()
        noise = Fractal2D(simplex.snoise2)
        return cls(noise.fractal, scale, segs_c, radius, max_depth, octaves, theme)

    def get_polygon_vertices(self, theta):
        rad = math.radians(theta)
        x = self.radius * math.cos(rad) + self.center.x
        y = self.radius * math.sin(rad) + self.center.y

        return Point3(x, y, 0)

    def generate_basic_polygon(self):
        """Generate vertices for the polygon that will form the ground.
        """
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
        lacunarity = 2.52    # 2.5

        for i in range(self.octaves):
            offset = offsets[i]
            fx = x * frequency + offset.x
            fy = y * frequency + offset.y
            noise = self.noise((fx + t) * self.scale, (fy + t) * self.scale)

            height += amplitude * noise
            frequency *= lacunarity
            amplitude *= persistence

        if self.theme == Island:
            r, _, _ = self.mask.get_gradient(x, y)
            height = 0 if r >= height else height - r  
        else:
            if height <= self.theme.LAYER_01.threshold:
                height = self.theme.LAYER_01.threshold

        # r, _, _ = self.mask.get_gradient(x, y)
        # if r >= height:
        #     height = 0
        # else:
        #     height = height - r

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
        if self.theme == Island:
            self.mask = RadialGradientMask(
                height=self.radius, width=self.radius, center_h=0, center_w=0)

        for v1, v2, v3 in self.generate_hills_and_valleys():
            # Each point's heights above "sea level". For a flat terrain,
            # it's just the vertical component of the respective vector.
            h1 = v1.z
            h2 = v2.z
            h3 = v3.z
            # import pdb; pdb.set_trace()
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
                    color = self.theme.color(v1_c.z)
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

                # interpolation value for v1 and v3
                # h is np.float64. if h1 - h3 == 0, t1 becomes -inf.
                t1 = 0 if (denom := h1 - h3) == 0 else (h1 - h) / denom
                # t1 = (h1 - h) / (h1 - h3)
                v1_c_n = self.lerp(v1_c, v3_c, t1)
                v1_b_n = self.lerp(v1_b, v3_b, t1)

                # interpolation value for v2 and v3
                # h is np.float64. if h2 - h3 == 0, t2 becomes -inf.
                t2 = 0 if (denom := h2 - h3) == 0 else (h2 - h) / denom
                # t2 = (h2 - h) / (h2 - h3)
                v2_c_n = self.lerp(v2_c, v3_c, t2)
                v2_b_n = self.lerp(v2_b, v3_b, t2)

                if points_above == 2:
                    color = self.theme.color(v1_c.z)
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
                    color = self.theme.color(v3_c.z)
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

    def get_geom_node(self):
        vdata_values = array.array('f', [])
        prim_indices = array.array('I', [])
        vertex_cnt = 0

        vertex_cnt += self.generate_terraced_terrain(vertex_cnt, vdata_values, prim_indices)
        # create a geom node.
        geom_node = self.create_geom_node(
            vertex_cnt, vdata_values, prim_indices, 'terraced_terrain')

        return geom_node