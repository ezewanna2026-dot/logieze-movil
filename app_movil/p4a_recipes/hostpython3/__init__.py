import os
import shutil
from os.path import dirname, join, exists, isdir

import pythonforandroid.recipes.hostpython3 as _base_module
from pythonforandroid.recipes.hostpython3 import HostPython3Recipe as _HostPython3Recipe

# p4a sets recipe_dir to THIS local directory, so patches must exist here.
# Copy everything from the built-in recipe directory so patches can be found.
_base_dir = dirname(_base_module.__file__)
_local_dir = dirname(__file__)
for _item in os.listdir(_base_dir):
    _src = join(_base_dir, _item)
    _dst = join(_local_dir, _item)
    if not exists(_dst):
        if isdir(_src):
            shutil.copytree(_src, _dst)
        else:
            shutil.copy2(_src, _dst)


class HostPython3Recipe(_HostPython3Recipe):
    version = '3.11.9'


recipe = HostPython3Recipe()
