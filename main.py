#!/usr/bin/env python3

from pathlib import Path

from tqdm import tqdm
import numpy as np

from src.parsecli import parseCli
from src.PicoParser import Parser


if __name__ == "__main__":
  args = parseCli()
  outDir = Path(args.outDir)

  for file in tqdm(args.files, desc="Files"):
    filePath = Path(file).expanduser()

    with Parser(filePath) as parser:
      if args.types:
        outDir.mkdir(parents=True, exist_ok=True)

        frameIndices = parser.scanFile()
        parsedList = parser.parseFile(frameIndices)
        timestampNp, csiNp, magNp, phaseNp = parser.timedCsi2numpy(parsedList)

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
