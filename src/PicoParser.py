from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Iterator, Iterable
import ctypes
import mmap
import os
import struct
import sys

import numpy as np

from .libpicoFrame import LibpicoRaw


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


class Parser:
  def __init__(self, filePath: Path) -> None:
    self.__filePath = filePath
    self.__file = open(self.__filePath, "rb")
    self.__fileMmap = mmap.mmap(self.__file.fileno(), 0, access=mmap.ACCESS_READ)
    self.__fileMmapView = memoryview(self.__fileMmap)

    self.__interpolatedSubcarrierIdx = np.array([-1, 0, 1])

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    self.__fileMmapView.release()
    self.__fileMmap.close()
    self.__file.close()

  def iterFrameIdx(self) -> Iterator[tuple[int, int]]:
    fileSize = os.path.getsize(self.__filePath)
    mmView = self.__fileMmapView

    idx = 0
    while idx + 4 <= fileSize:
      payloadLen = struct.unpack("<I", mmView[idx : idx + 4])[0]
      if payloadLen <= 0 or idx + (frameLength := 4 + payloadLen) > fileSize:
        break
      yield (idx, frameLength)
      idx += frameLength

  def parseFrames(
    self, frameIndices: Iterable[tuple[int, int]], nThread: int = 4
  ) -> list[tuple[np.datetime64, np.ndarray, np.ndarray, np.ndarray]]:
    maxWorkers = max(1, ((os.cpu_count() or 1) + 1) // 2)
    limitedWorkers = nThread if 0 < nThread < maxWorkers else maxWorkers

    with ThreadPoolExecutor(max_workers=limitedWorkers) as executor:
      timedCsi = list(executor.map(self.parseLibpicoFrame, frameIndices))
    return timedCsi

  def parseLibpicoFrame(
    self, frameIdx: tuple[int, int]
  ) -> tuple[np.datetime64, np.ndarray, np.ndarray, np.ndarray]:
    idx, length = frameIdx

    buffer = (ctypes.c_ubyte * length).from_buffer_copy(
      self.__fileMmapView[idx : idx + length]
    )
    libpicoRawPtr = libpico.getLibpicoFrameFromBuffer(buffer, length, True)

    timestamp, csiNp, magNp, phaseNp = self.libpicoFrame2timedCsi(
      libpicoRawPtr.contents
    )
    libpico.freeLibpicoFrame(libpicoRawPtr)
    return timestamp, csiNp, magNp, phaseNp

  def libpicoFrame2timedCsi(
    self, raw: LibpicoRaw, interpolate: bool = False
  ) -> tuple[np.datetime64, np.ndarray, np.ndarray, np.ndarray]:
    rawTimesteampNs: int = raw.rxSBasic.systemTime
    timestamp = np.datetime64(rawTimesteampNs, "ns")

    shape: tuple = (
      raw.csi.nTones,
      raw.csi.nTx,
      raw.csi.nRx,
      raw.csi.nEss + raw.csi.nCsi,
    )

    realNp = np.ctypeslib.as_array(raw.csi.csiRealPtr, shape)
    imgNp = np.ctypeslib.as_array(raw.csi.csiImagPtr, shape)
    csiNp = realNp + 1j * imgNp

    magNp = np.ctypeslib.as_array(raw.csi.magnitudePtr, shape)
    phaseNp = np.ctypeslib.as_array(raw.csi.phasePtr, shape)

    if not interpolate:
      subcarrierIdx = np.ctypeslib.as_array(
        raw.csi.subcarrierIndicesPtr, (raw.csi.subcarrierIndicesSize,)
      )
      csiNp = self.removeInterpolation(csiNp, subcarrierIdx)
      magNp = self.removeInterpolation(magNp, subcarrierIdx)
      phaseNp = self.removeInterpolation(phaseNp, subcarrierIdx)
    else:
      csiNp = csiNp.copy()
      magNp = magNp.copy()
      phaseNp = phaseNp.copy()

    return timestamp, csiNp, magNp, phaseNp

  def removeInterpolation(
    self, csi: np.ndarray, subcarrierIdx: np.ndarray
  ) -> np.ndarray:
    realSubcarrierIdx = np.nonzero(
      ~np.isin(subcarrierIdx, self.__interpolatedSubcarrierIdx)
    )[0]
    return csi[realSubcarrierIdx]
