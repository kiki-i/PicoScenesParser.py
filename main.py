#!/usr/bin/env python3

from datetime import datetime
from pathlib import Path
import glob

import numpy as np

from src.parsecli import parseCli
from src.PicoParser import Parser


def printInfo(info: str, indentLevel=0):
  now = datetime.now().strftime("%H:%M:%S")
  prefix = indentLevel * "  "
  if prefix != "":
    prefix = "|" + prefix[1:]
  print(f"[{now}] {prefix}{info}")


if __name__ == "__main__":
  args = parseCli()
  outDir = Path(args.output)

  fileList = []
  for path in args.input:
    fileList.extend(glob.glob(path, recursive=True))

  for file in fileList:
    filePath = Path(file).expanduser()
    printInfo(f"Converting {filePath.name}:")

    if any([args.timestamp, args.csi, args.magnitude, args.phase]):
      with Parser(filePath) as parser:
        outDir.mkdir(parents=True, exist_ok=True)

        printInfo("Parsing frames...", 1)
        timestampList, csiList, magList, phaseList = parser.parseFile(
          args.timestamp, args.csi, args.magnitude, args.phase, False
        )

      printInfo("Saving...", 1)
      if args.timestamp:
        filename = filePath.with_suffix(".tstamp.npy").name
        np.save(outDir / filename, timestampList)
        del timestampList
      if args.csi:
        filename = filePath.with_suffix(".csi.npy").name
        np.save(outDir / filename, csiList)
        del csiList
      if args.magnitude:
        filename = filePath.with_suffix(".mag.npy").name
        np.save(outDir / filename, magList)
        del magList
      if args.phase:
        filename = filePath.with_suffix(".phase.npy").name
        np.save(outDir / filename, phaseList)
        del phaseList
      printInfo("Done!", 1)

    else:
      printInfo("Nothing is enabled!", 1)
