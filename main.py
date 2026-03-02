#!/usr/bin/env python3

from datetime import datetime
from pathlib import Path
import argparse
import glob
import os

from picoparser import PicoParser
import numpy as np


def parseCli():
  description = "Convert PicoScenes .csi file to numpy .npy file"
  parser = argparse.ArgumentParser(description=description)
  parser.add_argument(
    "-i",
    "--input",
    type=str,
    nargs="+",
    metavar="",
    help="Specify input .csi file",
  )
  parser.add_argument(
    "-o",
    "--output",
    type=str,
    metavar="",
    default="out",
    help='Specify output directory, default = "out"',
  )
  parser.add_argument(
    "-c",
    "--csi",
    metavar="",
    action="store_const",
    const=True,
    default=False,
    help="Enable complex CSI output",
  )
  parser.add_argument(
    "-m",
    "--magnitude",
    metavar="",
    action="store_const",
    const=True,
    default=False,
    help="Enable magnitude output",
  )
  parser.add_argument(
    "-p",
    "--phase",
    metavar="",
    action="store_const",
    const=True,
    default=False,
    help="Enable phase output (with cyclic shift delay removed)",
  )
  parser.add_argument(
    "-t",
    "--timestamp",
    metavar="",
    action="store_const",
    const=True,
    default=False,
    help="Enable timestamp output",
  )
  return parser.parse_args()


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
      with PicoParser(filePath, os.cpu_count() // 2) as parser:
        outDir.mkdir(parents=True, exist_ok=True)

        printInfo("Parsing frames...", 1)
        tstampNdarray, csiNdarray, magNdarray, phaseNdarray = parser.getNdarray(
          args.timestamp, args.csi, args.magnitude, args.phase, False
        )

      printInfo("Saving...", 1)
      if tstampNdarray is not None:
        filename = filePath.with_suffix(".tstamp.npy").name
        np.save(outDir / filename, tstampNdarray)
        del tstampNdarray
      if csiNdarray is not None:
        filename = filePath.with_suffix(".csi.npy").name
        np.save(outDir / filename, csiNdarray)
        del csiNdarray
      if magNdarray is not None:
        filename = filePath.with_suffix(".mag.npy").name
        np.save(outDir / filename, magNdarray)
        del magNdarray
      if phaseNdarray is not None:
        filename = filePath.with_suffix(".phase.npy").name
        np.save(outDir / filename, phaseNdarray)
        del phaseNdarray
      printInfo("Done!", 1)

    else:
      printInfo("Nothing is enabled!", 1)
