import ctypes
import sys

from .LibpicoFrame import LibpicoRaw

if sys.platform == "win32":
  libpico = ctypes.CDLL("./libpico.dll")
else:
  libpico = ctypes.CDLL("./libpico.so")

libpico.getLibpicoFrameFromBuffer.restype = ctypes.POINTER(LibpicoRaw)
libpico.getLibpicoFrameFromBuffer.argtypes = [
  ctypes.POINTER(ctypes.c_uint8),
  ctypes.c_uint32,
  ctypes.c_bool,
]

libpico.freeLibpicoFrame.restype = ctypes.c_bool
libpico.freeLibpicoFrame.argtypes = [ctypes.POINTER(LibpicoRaw)]
