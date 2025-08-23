from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Iterator, Iterable
import ctypes
import mmap
import os
import struct

import numpy as np

from .libpico import libpico, LibpicoRaw


class Parser:
  __interpSubcarrierIdx = np.array([-1, 0, 1])

  def __init__(self, filePath: Path):
    self.__filePath = filePath

  def __enter__(self):
    self.__file = open(self.__filePath, "rb")
    self.__fileMmap = mmap.mmap(self.__file.fileno(), 0, access=mmap.ACCESS_READ)
    self.__fileMmapView = memoryview(self.__fileMmap)
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

  def iterFrame(
    self,
  ) -> Iterator[tuple[np.datetime64, np.ndarray, np.ndarray, np.ndarray]]:
    for idx in self.iterFrameIdx():
      yield self.parseLibpicoFrame(idx, True, True, True, True)

  def parseFile(
    self,
    enableTs: bool,
    enableCsi: bool,
    enableMag: bool,
    enablePhase: bool,
    interpolate: bool,
  ):
    return self.parseFrames(
      self.iterFrameIdx(),
      enableTs,
      enableCsi,
      enableMag,
      enablePhase,
      interpolate,
    )

  def parseFrames(
    self,
    frameIndices: Iterable[tuple[int, int]],
    enableTs: bool,
    enableCsi: bool,
    enableMag: bool,
    enablePhase: bool,
    interpolate: bool,
    nWorker: int = 4,
  ) -> Iterator:
    maxWorker = max(1, (os.cpu_count() or 1) // 2)

    with ThreadPoolExecutor(min(nWorker, maxWorker)) as executor:
      timedCsi = executor.map(
        lambda x: self.parseLibpicoFrame(
          x, enableTs, enableCsi, enableMag, enablePhase, interpolate
        ),
        frameIndices,
      )

    return zip(*timedCsi)

  def parseLibpicoFrame(
    self,
    frameIdx: tuple[int, int],
    enableTs: bool,
    enableCsi: bool,
    enableMag: bool,
    enablePhase: bool,
    interpolate: bool,
  ) -> tuple[
    np.datetime64 | None, np.ndarray | None, np.ndarray | None, np.ndarray | None
  ]:
    idx, length = frameIdx

    buffer = (ctypes.c_ubyte * length).from_buffer_copy(
      self.__fileMmapView[idx : idx + length]
    )
    libpicoRawPtr = libpico.getLibpicoFrameFromBuffer(buffer, length, True)

    timestamp, csiNp, magNp, phaseNp = self.libpicoFrame2Ndarray(
      libpicoRawPtr.contents, enableTs, enableCsi, enableMag, enablePhase, interpolate
    )
    libpico.freeLibpicoFrame(libpicoRawPtr)
    return timestamp, csiNp, magNp, phaseNp

  def libpicoFrame2Ndarray(
    self,
    raw: LibpicoRaw,
    enableTs: bool,
    enableCsi: bool,
    enableMag: bool,
    enablePhase: bool,
    interpolate: bool,
  ) -> tuple[
    np.datetime64 | None, np.ndarray | None, np.ndarray | None, np.ndarray | None
  ]:
    rawTimesteampNs: int = raw.rxSBasic.systemTime
    timestamp = np.datetime64(rawTimesteampNs, "ns") if enableTs else None

    shape: tuple = (
      raw.csi.nTones,
      raw.csi.nTx,
      raw.csi.nRx,
      raw.csi.nCsi + raw.csi.nEss,
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
      csiNp = self.removeInterp(csiNp, subcarrierIdx) if enableCsi else None
      magNp = self.removeInterp(magNp, subcarrierIdx) if enableMag else None
      phaseNp = self.removeInterp(phaseNp, subcarrierIdx) if enablePhase else None
    else:
      csiNp = csiNp.copy() if enableCsi else None
      magNp = magNp.copy() if enableMag else None
      phaseNp = phaseNp.copy() if enablePhase else None

    return timestamp, csiNp, magNp, phaseNp

  def removeInterp(self, csi: np.ndarray, subcarrierIdx: np.ndarray) -> np.ndarray:
    realSubcarrierIdx = np.nonzero(~np.isin(subcarrierIdx, self.__interpSubcarrierIdx))[
      0
    ]
    return csi[realSubcarrierIdx]
