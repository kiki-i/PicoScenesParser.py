#!/usr/bin/env python3

from pathlib import Path

from tqdm import tqdm
import numpy as np

from libpicoFrame import LibpicoRaw
from parsecli import parseCli
from PicoParser import Parser


def libpicoFrame2timedCsi(
  raw: LibpicoRaw, interpolate: bool = False
) -> tuple[np.datetime64, np.ndarray, np.ndarray, np.ndarray]:
  rawTimesteampNs: int = raw.rxSBasic.systemTime
  timestamp = np.datetime64(rawTimesteampNs, "ns")

  shape: tuple = (raw.csi.nTones, raw.csi.nTx, raw.csi.nRx)
  csiSize = raw.csi.csiSize
  realNp = np.array([raw.csi.csiRealPtr[i] for i in range(csiSize)], dtype=np.float32)
  imgNp = np.array([raw.csi.csiImagPtr[i] for i in range(csiSize)], dtype=np.float32)
  csiNp = realNp + 1j * imgNp
  csiNp = csiNp.reshape(shape)

  magnitudeSize = raw.csi.magnitudeSize
  magNp = np.array(
    [raw.csi.magnitudePtr[i] for i in range(magnitudeSize)], dtype=np.float32
  )
  magNp = magNp.reshape(shape)

  phaseSize = raw.csi.phaseSize
  phaseNp = np.array([raw.csi.phasePtr[i] for i in range(phaseSize)], dtype=np.float32)
  phaseNp = phaseNp.reshape(shape)

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


def appendDict(d: dict[str, list], k: str, v, create: bool = False):
  if k in d:
    d[k].append(v)
  else:
    if create:
      d[k] = [v]


if __name__ == "__main__":
  args = parseCli()
  outDir = Path(args.outDir)

  parser = Parser()
  for file in tqdm(args.files, desc="Files"):
    filePath = Path(file).expanduser()
    if args.types:
      outDir.mkdir(parents=True, exist_ok=True)
      outDict = {x: [] for x in args.types}

      for libpicoFrame in parser.parseFile(filePath):
        timestamp, csi, mag, phase = libpicoFrame2timedCsi(libpicoFrame)
        appendDict(outDict, "timestamp", timestamp)
        appendDict(outDict, "csi", csi)
        appendDict(outDict, "mag", mag)
        appendDict(outDict, "phase", phase)

      for dataType in outDict.keys():
        filename = filePath.with_suffix(f".{dataType}.npy").name
        np.save(outDir / filename, outDict[dataType])
