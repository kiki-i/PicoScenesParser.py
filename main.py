#!/usr/bin/env python3

from datetime import datetime
from pathlib import Path

import numpy as np

from src.parsecli import parseCli
from src.PicoParser import Parser


def nowStr() -> str:
  return datetime.now().strftime("[%H:%M:%S]")


if __name__ == "__main__":
  args = parseCli()
  outDir = Path(args.outDir)

  for file in args.files:
    filePath = Path(file).expanduser()
    print(f"{nowStr()} Convert {filePath.name}...")

    with Parser(filePath) as parser:
      if args.types:
        outDir.mkdir(parents=True, exist_ok=True)

        frameIndices = parser.iterFrameIdx()
        timestampList, csiList, magList, phaseList = zip(
          *parser.parseFrames(frameIndices)
        )

        if "timestamp" in args.types:
          filename = filePath.with_suffix(".timestamp.npy").name
          np.save(outDir / filename, timestampList)
          del timestampList
        if "csi" in args.types:
          filename = filePath.with_suffix(".csi.npy").name
          np.save(outDir / filename, csiList)
          del csiList
        if "mag" in args.types:
          filename = filePath.with_suffix(".mag.npy").name
          np.save(outDir / filename, magList)
          del magList
        if "phase" in args.types:
          filename = filePath.with_suffix(".phase.npy").name
          np.save(outDir / filename, phaseList)
          del phaseList

    print(f"{nowStr()} Done!")
