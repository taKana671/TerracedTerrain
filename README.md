# TerracedTerrain

This repository uses the meandering triangles algorithm to create a 3D model of terraced terrain. 
The polygon that forms the ground is repeatedly divided into triangles, and noise such as simplex and cellular is used to calculate the height of each vertex. 
Then, the meandering triangles algorithm is used to form a staircase-like terrain.
The terrain is colored by setting color information directly to the vertices.
In addition, by running `terraced_terrain.py`, you can create a 3D model while checking how the terrain changes depending on the parameters.
<br/><br/>
The meandering triangles algorithm is based on https://icospheric.com/blog/2016/07/17/making-terraced-terrain/.

![Image](https://github.com/user-attachments/assets/9de4eeef-a28e-41b7-ab28-04bae225088d)

# Requirements

* Panda3D 1.10.15
* numpy 2.2.4
* Cython 3.0.12
* opencv-contrib-python 4.11.0.86
* opencv-python 4.11.0.86
  
# Environment

* Python 3.12
* Windows11

# Usage

### Clone this repository with submodule.
```
git clone --recursive https://github.com/taKana671/TerracedTerrain.git
```

### Build cython code.

If cytnon code is not built, noise is calculated using python code.
```
cd TerracedTerrain
python setup.py build_ext --inplace
```

If the error like "ModuleNotFoundError: No module named ‘distutils’" occurs, install the setuptools.
```
pip install setuptools
```

### Code sample

Create an instance of TerracedTerrainGenerator and call the create method to return the NodePath of the terrain's 3D model. 
If you use the class methods from_simplex, from_cellular, or from_perlin, you do not need to specify noise among the following [parameters](#parameters).

```
from terraced_terrain_generator import TerracedTerrainGenerator

generator = TerracedTerrainGenerator.from_simplex()     # simplexNoise is specified.
# generator = TerracedTerrainGenerator.from_cellular()  # CellularNoise is specified.
# generator = TerracedTerrainGenerator.from_perlin()    # PerlinNoise is specified.

model = generator.create()
```

### Parameters

* _noise: func_
  * Function that generates noise.

* _scale: float_
  * The smaller this value is, the more sparse the noise becomes; default value is 10.
    
* _segs_s: int_
  * The number of vertices in the polygon that forms the ground; minimum is 3; defalut is 5.

* _radius: float_
  * Length from the center of the polygon forming the ground to each vertex; default is 3.

* _max_depth: int_
  * The number of times that triangles, which formed by the center point and each vertex of the ground polygon, are further divided into triangles; default is 6.

* _octaves: int_
  * The number of loops to calculate the height of the vertex coordinates; default is 3.

* theme: str_
  * one of "mountain", "snowmountain" and "desert"; default is mountain.
 
### Usage of terraced_terrain.py

Run terraced_terrain.py and select the noise and theme using the checkboxes. 
If you want to change the parameters, edit the values in the entry boxes and click the [reflet] button.

```
python terraced_terrain.py
```

![Image](https://github.com/user-attachments/assets/d1f98aab-b113-4be0-b50a-4e79d49bc580)

