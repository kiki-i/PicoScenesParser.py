from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import ctypes
import io
import itertools
import os
import struct
import sys

import numpy as np

from libpicoFrame import LibpicoRaw


def libpicoFrame2timedCsi(
  raw: LibpicoRaw, interpolate: bool = False
) -> tuple[np.datetime64, np.ndarray, np.ndarray, np.ndarray]:
  rawTimesteampNs: int = raw.rxSBasic.systemTime
  timestamp = np.datetime64(rawTimesteampNs, "ns")

  shape: tuple = (raw.csi.nTones, raw.csi.nTx, raw.csi.nRx)
  csiSize = raw.csi.csiSize
  # realNp = np.array([raw.csi.csiRealPtr[i] for i in range(csiSize)], dtype=np.float32)
  # imgNp = np.array([raw.csi.csiImagPtr[i] for i in range(csiSize)], dtype=np.float32)
  realNp = np.frombuffer(
    (ctypes.c_float * csiSize).from_address(
      ctypes.addressof(raw.csi.csiRealPtr.contents)
    ),
    dtype=np.float32,
  )
  imgNp = np.frombuffer(
    (ctypes.c_float * csiSize).from_address(
      ctypes.addressof(raw.csi.csiImagPtr.contents)
    ),
    dtype=np.float32,
  )
  csiNp = realNp + 1j * imgNp
  csiNp = csiNp.reshape(shape)

  magnitudeSize = raw.csi.magnitudeSize
  # magNp = np.array(
  #   [raw.csi.magnitudePtr[i] for i in range(magnitudeSize)], dtype=np.float32
  # ).reshape(shape)
  magNp = np.frombuffer(
    (ctypes.c_float * magnitudeSize).from_address(
      ctypes.addressof(raw.csi.magnitudePtr.contents)
    ),
    dtype=np.float32,
  ).reshape(shape)

  phaseSize = raw.csi.phaseSize
  # phaseNp = np.array([raw.csi.phasePtr[i] for i in range(phaseSize)], dtype=np.float32).reshape(shape)
  phaseNp = np.frombuffer(
    (ctypes.c_float * phaseSize).from_address(
      ctypes.addressof(raw.csi.phasePtr.contents)
    ),
    dtype=np.float32,
  ).reshape(shape)

  if not interpolate:
    size = raw.csi.subcarrierIndicesSize
    subcarrierIdx = tuple(raw.csi.subcarrierIndicesPtr[i] for i in range(size))
    csiNp = removeInterpolation(csiNp, subcarrierIdx)
    magNp = removeInterpolation(magNp, subcarrierIdx)
    phaseNp = removeInterpolation(phaseNp, subcarrierIdx)

  return timestamp, csiNp, magNp, phaseNp


def removeInterpolation(csi: np.ndarray, subcarrierIdx: tuple) -> np.ndarray:
  interpolatedSubcarrierIdx = (-1, 0, 1)
  realSubcarrierIdx = np.nonzero(~np.isin(subcarrierIdx, interpolatedSubcarrierIdx))
  return csi[realSubcarrierIdx]


class Parser:
  def __init__(self) -> None:
    self.__initLib()

    self._payloadLenBuffer = bytearray(4)

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

  def scanFile(self, filePath: Path) -> list[tuple[int, int]]:
    fileSize = os.path.getsize(filePath)

    frameIndices: list[tuple[int, int]] = []
    with open(filePath, "rb") as f:
      while True:
        idx = f.tell()

        n = f.readinto(self._payloadLenBuffer)
        if n != 4:
          break

        payloadLen = struct.unpack("<I", self._payloadLenBuffer)[0]
        if payloadLen <= 0:
          break

        frameLength = 4 + payloadLen
        f.seek(payloadLen, 1)
        if f.tell() > fileSize:
          break

        frameIndices.append((idx, frameLength))

    return frameIndices

  def parseFile(
    self, filePath: Path, frameIndices: list[tuple[int, int]], nThread: int = 0
  ) -> list[tuple[np.datetime64, np.ndarray, np.ndarray, np.ndarray]]:
    maxWorkers = os.cpu_count()
    maxWorkers = maxWorkers if maxWorkers else 1
    maxWorkers = (maxWorkers + 1) // 2

    nWorkers = nThread if nThread > 0 and nThread < maxWorkers else maxWorkers
    # timedCsi = list(map(self.parseLibpicoFrame, itertools.repeat(f), frameIndices))
    with ThreadPoolExecutor(max_workers=nWorkers) as executor:
      timedCsi = list(
        executor.map(self.parseLibpicoFrame, itertools.repeat(filePath), frameIndices)
      )
    return timedCsi

  def parseLibpicoFrame(
    self, filePath: Path, frameIdx: tuple[int, int]
  ) -> tuple[np.datetime64, np.ndarray, np.ndarray, np.ndarray]:
    with open(filePath, "rb") as f:
      idx, length = frameIdx

      buffer = (ctypes.c_ubyte * length)()
      bufferMv = memoryview(buffer)

      f.seek(idx)
      f.readinto(bufferMv)
      libpicoRawPtr = self.__lib.getLibpicoCsiFromBuffer(buffer, length, True)

      return libpicoFrame2timedCsi(libpicoRawPtr.contents)
