from pathlib import Path
from typing import Iterator
import ctypes
import os
import struct
import sys

from libpicoFrame import LibpicoRaw


class Parser:
  def __init__(self) -> None:
    self.__initLib()

    self._payloadLenBuffer = bytearray(4)
    self.__bufferSize = 1 << 16
    self.__buffer = (ctypes.c_ubyte * self.__bufferSize)()
    self.__bufferMv = memoryview(self.__buffer)

  def __initLib(self) -> None:
    if sys.platform == "win32":
      lib = ctypes.CDLL("./libpico.dll")
    else:
      lib = ctypes.CDLL("./libpico.so")

    lib.getLibpicoCsiFromBuffer.restype = ctypes.POINTER(LibpicoRaw)
    lib.getLibpicoCsiFromBuffer.argtypes = [
      ctypes.POINTER(ctypes.c_uint8),
      ctypes.c_uint32,
      ctypes.c_bool,
    ]

    lib.freeLibpicoRaw.restype = ctypes.c_bool
    lib.freeLibpicoRaw.argtypes = [ctypes.POINTER(LibpicoRaw)]

    self.__lib = lib

  def __increaseBuffer(self, length: int):
    if len(self.__buffer) < length:
      self.__buffer = (ctypes.c_ubyte * length)()
      self.__bufferMv = memoryview(self.__buffer)
      self.__bufferSize = length

  def parseFile(self, filePath: Path) -> Iterator[LibpicoRaw]:
    fileSize = os.path.getsize(filePath)

    with open(filePath, "rb") as f:
      while True:
        n = f.readinto(self._payloadLenBuffer)
        if n != 4:
          break

        payloadLen = struct.unpack("<I", self._payloadLenBuffer)[0]
        if payloadLen <= 0 or f.tell() + payloadLen > fileSize:
          break

        length = 4 + payloadLen
        self.__increaseBuffer(length)
        self.__buffer[:4] = self._payloadLenBuffer
        n = f.readinto(self.__bufferMv[4 : 4 + payloadLen])
        if n != payloadLen:
          break

        libpicoRawPtr = self.__lib.getLibpicoCsiFromBuffer(self.__buffer, length, True)

        if libpicoRawPtr is None:
          break
        out = LibpicoRaw()
        ctypes.memmove(
          ctypes.addressof(out),
          libpicoRawPtr,
          ctypes.sizeof(out),
        )
        yield out
        self.__lib.freeLibpicoRaw(libpicoRawPtr)
