from distutils.core import setup, Extension
from Cython.Build import cythonize


# extensions = [
#     Extension(
#         '*',
#         ['noise/cynoise/*.pyx', 'noise/cynoise/voronoi/*.pyx'],
#         define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")]
#     )
# ]

# setup(
#     ext_modules=cythonize(
#         extensions,
#         compiler_directives={'profile': False}
#     )
# )




import glob
import pathlib

from distutils.core import setup, Extension
from Cython.Build import cythonize


def create_ext():
    for p in glob.iglob('noise/cynoise/**/*pyx', recursive=True):
        path = pathlib.Path(p)

        name = path.name
        posix_path = path.as_posix()
        parents = posix_path.split('/')[:-1]

        yield Extension(
            f'{".".join(parents)}.{name.split(".")[0]}',
            [f'{"/".join(parents)}/{name}'],
            define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")]
        )


extensions = [ext for ext in create_ext()]

setup(
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            'profile': False,
            'language_level': "3"
        }
    )
)
