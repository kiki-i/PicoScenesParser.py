from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
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

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    self.__fileMmapView.release()
    self.__fileMmap.close()
    self.__file.close()

  def scanFile(self) -> list[tuple[int, int]]:
    fileSize = os.path.getsize(self.__filePath)
    frameIndices: list[tuple[int, int]] = []

    mmView = self.__fileMmapView
    idx = 0
    while idx + 4 <= fileSize:
      payloadLenBuffer = mmView[idx : idx + 4]
      payloadLen = struct.unpack("<I", payloadLenBuffer)[0]
      if payloadLen <= 0 or idx + (frameLength := 4 + payloadLen) > fileSize:
        break
      frameIndices.append((idx, frameLength))
      idx += frameLength

    return frameIndices

  def parseFile(
    self, frameIndices: list[tuple[int, int]], nThread: int = 4
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

    shape: tuple = (raw.csi.nTones, raw.csi.nTx, raw.csi.nRx)

    csiSize = raw.csi.csiSize
    realNp = self.npFromFloatPtr(raw.csi.csiRealPtr, csiSize)
    imgNp = self.npFromFloatPtr(raw.csi.csiImagPtr, csiSize)
    csiNp = realNp + 1j * imgNp
    csiNp = csiNp.reshape(shape)

    magNp = self.npFromFloatPtr(raw.csi.magnitudePtr, raw.csi.magnitudeSize).reshape(
      shape
    )
    phaseNp = self.npFromFloatPtr(raw.csi.phasePtr, raw.csi.phaseSize).reshape(shape)

    if not interpolate:
      size = raw.csi.subcarrierIndicesSize
      subcarrierIdx = tuple(raw.csi.subcarrierIndicesPtr[i] for i in range(size))
      csiNp = self.removeInterpolation(csiNp, subcarrierIdx)
      magNp = self.removeInterpolation(magNp, subcarrierIdx)
      phaseNp = self.removeInterpolation(phaseNp, subcarrierIdx)
    else:
      csiNp = csiNp.copy()
      magNp = magNp.copy()
      phaseNp = phaseNp.copy()

    return timestamp, csiNp, magNp, phaseNp

  @staticmethod
  def npFromFloatPtr(ptr, size, dtype=np.float32) -> np.ndarray:
    return np.frombuffer(
      (ctypes.c_float * size).from_address(ctypes.addressof(ptr.contents)),
      dtype=dtype,
    )

  @staticmethod
  def removeInterpolation(csi: np.ndarray, subcarrierIdx: tuple) -> np.ndarray:
    interpolatedSubcarrierIdx = (-1, 0, 1)
    realSubcarrierIdx = np.nonzero(~np.isin(subcarrierIdx, interpolatedSubcarrierIdx))
    return csi[realSubcarrierIdx]

  @staticmethod
  def timedCsi2numpy(
    dataList: list[tuple[np.datetime64, np.ndarray, np.ndarray, np.ndarray]],
  ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    timestampNp = np.array([x[0] for x in dataList])
    csiNp = np.array([x[1] for x in dataList])
    magNp = np.array([x[2] for x in dataList])
    phaseNp = np.array([x[3] for x in dataList])

    return timestampNp, csiNp, magNp, phaseNp
