import array
import math
import random

from panda3d.core import Vec3, Point3, Vec2

from .create_geometry import ProceduralGeometry
from panda3d.core import NodePath
from panda3d.core import Geom, GeomNode, GeomTriangles
from panda3d.core import Mat4, Vec3
from panda3d.core import GeomVertexFormat, GeomVertexData, GeomVertexArrayFormat


from noise import SimplexNoise, PerlinNoise, CellularNoise


class PentagonalDivision(ProceduralGeometry):

    def __init__(self):
        super().__init__()
        self.center = Point3(0, 0, 0)
        self.max_depth = 6
        self.radius = 3
        self.octaves = 3
        self.noise = SimplexNoise()
        # self.noise = PerlinNoise()
        # self.noise = CellularNoise()

    def generate_pentagon_vertices(self):
        deg = 72

        for i in range(5):
            theta = deg * (i + 1)
            rad = math.radians(theta)
            x = self.radius * math.cos(rad) + self.center.x
            y = self.radius * math.sin(rad) + self.center.y
            yield Point3(x, y, 0)

    def calc_midpoints(self, tri):
        for p1, p2 in zip(tri, tri[1:] + tri[:1]):
            yield (p1 + p2) / 2

    def recursive_divide(self, tri, depth=1):
        if depth == self.max_depth:
            yield tri
        else:
            midpoints = [p for p in self.calc_midpoints(tri)]

            for i, vert in enumerate(tri):
                ii = n if (n := i - 1) >= 0 else len(midpoints) - 1
                divided = [vert, midpoints[i], midpoints[ii]]
                yield from self.recursive_divide(divided, depth + 1)
            yield from self.recursive_divide(midpoints, depth + 1)

    # def create_penta(self, vertex_cnt, vdata_values, prim_indices):
    def create_penta(self):
        pentagon = [p for p in self.generate_pentagon_vertices()]
        offsets = [Vec2(random.randint(-1000, 1000),
                        random.randint(-1000, 1000)) for _ in range(self.octaves)]
        # offsets = Vec2(random.randint(-1000, 1000),
        #                 random.randint(-1000, 1000))

        start = 0

        for pt1, pt2 in zip(pentagon, pentagon[1:] + pentagon[:1]):
            for tri in self.recursive_divide([pt1, pt2, self.center]):
                for vert in tri:
                    z = self.get_height(vert.x, vert.y, offsets)
                    vert.z = z
                yield tri

        #             vdata_values.extend(vert)
        #             vdata_values.extend(self.color)
        #             vdata_values.extend(Point3(0, 0, 1))
        #             vdata_values.extend((0, 0))
        #             vertex_cnt += 1

        #         indices = (start, start + 1, start + 2)
        #         prim_indices.extend(indices)
        #         start += 3

        # return vertex_cnt

    def get_height(self, x, y, offsets):
        height = 0
        amplitude = 1.0
        frequency = 0.055
        persistence = 0.375  # 0.5
        lacunarity = 2.52  # 2.5
        scale = 10

        for i in range(self.octaves):
            offset = offsets[i]
            fx = x * frequency + offset.x
            fy = y * frequency + offset.y

            # simplex
            # noise = self.noise.snoise2(fx * scale, fy * scale)
            noise = self.noise.snoise2((fx / self.radius * 2 + 123) * scale, (fy / self.radius * 2 + 123) * scale)

            # perlin
            # noise = self.noise.pnoise2((fx / self.radius * 2 + 123) * scale, (fy / self.radius * 2 + 123) * scale)

            # cellular
            # noise = self.noise.fdist2((fx / self.radius * 2 + 123) * scale, (fy / self.radius * 2 + 123) * scale)


            height += amplitude * noise
            frequency *= lacunarity
            amplitude *= persistence

        return height

    def get_height2(self, x, y, offsets):
        frequency = 0.2
        height = 5

        fx = (x + offsets.x) * frequency
        fy = (y + offsets.y) * frequency
        return height * self.noise.snoise2((fx / 8) * 20, (fy / 8) * 20)

    def terraced(self, triangles, vertex_cnt, vdata_values, prim_indices):
    # def terraced(self, vertex_cnt, vdata_values, prim_indices):

        # length = len(vdata_values)

        for v1, v2, v3 in triangles:
            h1 = v1.z
            h2 = v2.z
            h3 = v3.z

            # h_min = math.floor(min(h1, h2, h3))
            # h_max = math.floor(max(h1, h2, h3))
            li = [int(h1 * 10), int(h2 * 10), int(h3 * 10)]
            h_min = math.floor(min(li))
            h_max = math.floor(max(li))
            # import pdb; pdb.set_trace()
            # print(h_min, h_max, h1, h2, h3)
            for h in range(h_min, h_max + 1):
                h *= 0.1
                points_above = 0

                if h1 < h:
                    if h2 < h:
                        if h3 >= h:
                            points_above = 1
                    else:
                        if h3 < h:
                            points_above = 1
                            v1, v2, v3 = v3, v1, v2
                        else:
                            points_above = 2
                            v1, v2, v3 = v2, v3, v1
                else:
                    if h2 < h:
                        if h3 < h:
                            points_above = 1
                            v1, v2, v3 = v2, v3, v1
                        else:
                            points_above = 2
                            v1, v2, v3 = v3, v1, v2
                    else:
                        if h3 < h:
                            points_above = 2
                        else:
                            points_above = 3
                h1 = v1.z
                h2 = v2.z
                h3 = v3.z
                v1_c = Point3(v1.x, v1.y, h)
                v2_c = Point3(v2.x, v2.y, h)
                v3_c = Point3(v3.x, v3.y, h)
                
                # v1_b = Point3(v1.x, v1.y, h - 1)
                # v2_b = Point3(v2.x, v2.y, h - 1)
                # v3_b = Point3(v3.x, v3.y, h - 1)
                v1_b = Point3(v1.x, v1.y, h - 0.1)
                v2_b = Point3(v2.x, v2.y, h - 0.1)
                v3_b = Point3(v3.x, v3.y, h - 0.1)

                # if points_above == 0:
                if points_above == 3:
                    # if vertex_cnt >= 65533:
                    #     break

                    # print('above point 3')
                    for vert in [v1_c, v2_c, v3_c]:
                        vdata_values.extend(vert)
                        vdata_values.extend(self.color)
                        vdata_values.extend(Point3(0, 0, 1))

                        u, v = self.calc_uv(vert.x, vert.y)                        
                        vdata_values.extend((u, v))
                        # vdata_values.extend((0, 0))
                        # print(vert)

                    indices = (vertex_cnt, vertex_cnt + 1, vertex_cnt + 2)
                    # try:
                    prim_indices.extend(indices)
                    # except Exception:
                    #     import pdb; pdb.set_trace()

                    vertex_cnt += 3
                else:
                    t1 = (h1 - h) / (h1 - h3)
                    v1_c_n = self.lerp(v1_c, v3_c, t1)
                    v1_b_n = self.lerp(v1_b, v3_b, t1)

                    t2 = (h2 - h) / (h2 - h3)
                    v2_c_n = self.lerp(v2_c, v3_c, t2)
                    v2_b_n = self.lerp(v2_b, v3_b, t2)

                    if points_above == 2:
                        # print('above point 2')
                        # add roof part of the step
                        for vert in [v1_c, v2_c, v2_c_n, v1_c_n]:
                            vdata_values.extend(vert)
                            vdata_values.extend(self.color)
                            vdata_values.extend(Point3(0, 0, 1))

                            u, v = self.calc_uv(vert.x, vert.y)
                            vdata_values.extend((u, v))
                            # vdata_values.extend((0, 0))

                        prim_indices.extend([vertex_cnt, vertex_cnt + 1, vertex_cnt + 2])
                        prim_indices.extend([vertex_cnt + 2, vertex_cnt + 3, vertex_cnt])
                        vertex_cnt += 4

                        # add wall part if the step
                        for vert in [v1_c_n, v2_c_n, v2_b_n, v1_b_n]:
                            vdata_values.extend(vert)
                            vdata_values.extend(self.color)

                            normal = Vec3(vert.x, vert.y, 0).normalized()
                            vdata_values.extend(normal)
                            # vdata_values.extend(Point3(1, 0, 0))

                            u, v = self.calc_uv(vert.x, vert.y)
                            vdata_values.extend((u, v))
                            # vdata_values.extend((0, 0))

                        prim_indices.extend([vertex_cnt, vertex_cnt + 1, vertex_cnt + 2])
                        prim_indices.extend([vertex_cnt, vertex_cnt + 2, vertex_cnt + 3])
                        vertex_cnt += 4

                    elif points_above == 1:
                        # add roof part of the step
                        for vert in [v3_c, v1_c_n, v2_c_n]:
                            vdata_values.extend(vert)
                            vdata_values.extend(self.color)
                            vdata_values.extend(Point3(0, 0, 1))

                            u, v = self.calc_uv(vert.x, vert.y)
                            vdata_values.extend((u, v))
                            # vdata_values.extend((0, 0))

                        prim_indices.extend([vertex_cnt, vertex_cnt + 1, vertex_cnt + 2])
                        vertex_cnt += 3

                        # add wall part if the step
                        for vert in [v2_c_n, v1_c_n, v1_b_n, v2_b_n]:
                            vdata_values.extend(vert)
                            vdata_values.extend(self.color)

                            normal = Vec3(vert.x, vert.y, 0).normalized()
                            vdata_values.extend(normal)
                            # vdata_values.extend(Point3(1, 0, 0))

                            u, v = self.calc_uv(vert.x, vert.y)
                            vdata_values.extend((u, v))
                            # vdata_values.extend((0, 0))

                        # print(vertex_cnt)
                        prim_indices.extend([vertex_cnt, vertex_cnt + 1, vertex_cnt + 3])
                        prim_indices.extend([vertex_cnt + 1, vertex_cnt + 2, vertex_cnt + 3])
                        vertex_cnt += 4


        return vertex_cnt

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
        # self.define_variables()

        # Create an outer cylinder.
        vdata_values = array.array('f', [])
        # prim_indices = array.array('H', [])
        prim_indices = array.array('I', [])
        vertex_cnt = 0

        # vertex_cnt = self.create_penta(
        #     vertex_cnt, vdata_values, prim_indices)
        # import pdb; pdb.set_trace()
        # vertex_cnt = self.terraced(vertex_cnt, vdata_values, prim_indices)
        triangles = [tri for tri in self.create_penta()]
        vertex_cnt = self.terraced(triangles, 0, vdata_values, prim_indices)

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

    # ################ wireframe of like terrain #########################
    # def create_penta(self, vertex_cnt, vdata_values, prim_indices):
    #     r = 2
    #     pentagon = [p for p in self.generate_pentagon_vertices(r)]
    #     start = 0

    #     for pt1, pt2 in zip(pentagon, pentagon[1:] + pentagon[:1]):
    #         for tri in self.recursive_divide([pt1, pt2, self.center]):
    #             for vert in tri:
    #                 vdata_values.extend(vert)
    #                 vdata_values.extend(self.color)
    #                 vdata_values.extend(Point3(0, 0, 1))
    #                 vdata_values.extend((0, 0))
    #                 vertex_cnt += 1

    #             indices = (start, start + 1, start + 2)
    #             prim_indices.extend(indices)
    #             start += 3

    #     return vertex_cnt

    # def get_height(self, x, y, offsets, octaves=3):
    #     # height = 0
    #     height = 1
    #     amplitude = 1.0
    #     frequency = 0.055
    #     persistence = 0.375  # 0.5
    #     lacunarity = 2.52  # 2.5
    #     scale = 20

    #     for i in range(octaves):
    #         offset = offsets[i]
    #         fx = x * frequency + offset.x
    #         fy = y * frequency + offset.y
    #         noise = self.noise.snoise2(fx * scale, fy * scale)
    #         height += amplitude * noise
    #         frequency *= lacunarity
    #         amplitude *= persistence

    #     return height

    # def get_height2(self, x, y, offsets):
    #     frequency = 0.2
    #     height = 5

    #     fx = (x + offsets.x) * frequency
    #     fy = (y + offsets.y) * frequency
    #     return height * self.noise.snoise2((fx / 4) * 10, (fy / 4) * 10)

    # def get_geom_node(self):
    #     # self.define_variables()

    #     # Create an outer cylinder.
    #     vdata_values = array.array('f', [])
    #     prim_indices = array.array('H', [])
    #     vertex_cnt = 0

    #     vertex_cnt = self.create_penta(
    #         vertex_cnt, vdata_values, prim_indices)

    #     offsets = [Vec2(random.randint(-1000, 1000),
    #                     random.randint(-1000, 1000)) for _ in range(3)]

    #     # offsets = Vec2(random.randint(-1000, 1000),
    #     #                random.randint(-1000, 1000))

    #     for i in range(0, len(vdata_values), self.stride):
    #         x = vdata_values[i]
    #         y = vdata_values[i + 1]
    #         z = self.get_height(x, y, offsets)
    #         vdata_values[i + 2] = z

    #     # Create the geom node.
    #     geom_node = self.create_geom_node(
    #         vertex_cnt, vdata_values, prim_indices, 'terrace')
    #     return geom_node
