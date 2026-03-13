# PicoScenesParser.py

Convert PicoScenes `.csi` file to numpy `.npy` file with multithreaded parsing. Provides **faster** performance with significantly **lower memory usage** compared to [PicoScenes-Python-Toolbox](https://github.com/wifisensing/PicoScenes-Python-Toolbox).

An example using the [PicoParser.py](https://github.com/kiki-i/PicoParser.py) library.

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

* [PicoParser.py](https://github.com/kiki-i/PicoParser.py): Install the library according its `README.md`.
* numpy

## If you find this helpful

Please cite [**my works**](https://scholar.google.com/citations?user=XiudsEIAAAAJ).

## License

[![AGPLv3](https://www.gnu.org/graphics/agplv3-with-text-162x68.png)](https://www.gnu.org/licenses/agpl-3.0.html)

Licensed under the [AGPLv3](https://www.gnu.org/licenses/agpl-3.0.html).
