#!/usr/bin/env python3

from pathlib import Path

from tqdm import tqdm
import numpy as np

from parsecli import parseCli
from PicoParser import Parser


def timedCsi2numpy(
  dataList: list[tuple[np.datetime64, np.ndarray, np.ndarray, np.ndarray]],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
  timestampNp = np.array([x[0] for x in dataList])
  csiNp = np.array([x[1] for x in dataList])
  magNp = np.array([x[2] for x in dataList])
  phaseNp = np.array([x[3] for x in dataList])

  return timestampNp, csiNp, magNp, phaseNp


if __name__ == "__main__":
  args = parseCli()
  outDir = Path(args.outDir)

  parser = Parser()
  for file in tqdm(args.files, desc="Files"):
    filePath = Path(file).expanduser()
    if args.types:
      outDir.mkdir(parents=True, exist_ok=True)

      frameIndices = parser.scanFile(filePath)
      parsedList = parser.parseFile(filePath, frameIndices)
      timestampNp, csiNp, magNp, phaseNp = timedCsi2numpy(parsedList)

      if "timestamp" in args.types:
        filename = filePath.with_suffix(".timestamp.npy").name
        np.save(outDir / filename, timestampNp)
      if "csi" in args.types:
        filename = filePath.with_suffix(".csi.npy").name
        np.save(outDir / filename, csiNp)
      if "mag" in args.types:
        filename = filePath.with_suffix(".mag.npy").name
        np.save(outDir / filename, magNp)
      if "phase" in args.types:
        filename = filePath.with_suffix(".phase.npy").name
        np.save(outDir / filename, phaseNp)
