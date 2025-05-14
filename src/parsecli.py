import argparse


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
