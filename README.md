# PicoScenesToolbox.py

Convert PicoScenes `.csi` file to numpy `.npy` file with multithreaded parsing. Significantly reduce memory usage compared to [PicoScenes-Python-Toolbox](https://github.com/wifisensing/PicoScenes-Python-Toolbox).

An example using [libpico](https://github.com/kiki-i/libpico) library.

## Usage

```
optional arguments:
  -h, --help       show this help message and exit
  -i, --input      Specify input .csi file
  -o, --output     Specify output directory, default = "out"
  -c, --csi        Enable complex CSI output
  -m, --magnitude  Enable magnitude output
  -p, --phase      Enable phase output (with cyclic shift delay removed)
  -t, --timestamp  Enable timestamp output
```

## Dependencies

* [libpico](https://github.com/kiki-i/libpico): Copy `libpico.dll` (Windows) or `libpico.so`  (Linux) to the same dictionary as `PicoScenesToolbox.py/main.py`.
* numpy

## License

[![AGPLv3](https://www.gnu.org/graphics/agplv3-with-text-162x68.png)](https://www.gnu.org/licenses/agpl-3.0.html)

Licensed under the [AGPLv3](https://www.gnu.org/licenses/agpl-3.0.html).
