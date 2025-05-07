import ctypes


class LibpicoMeta(ctypes.Structure):
  _pack_ = 1
  _fields_ = [("hasData", ctypes.c_uint8)]


class Ieee80211MacFrameHeaderControlField(ctypes.Structure):
  _pack_ = 1
  _fields_ = [
    ("version", ctypes.c_uint16),
    ("type", ctypes.c_uint16),
    ("subtype", ctypes.c_uint16),
    ("toDS", ctypes.c_uint16),
    ("fromDS", ctypes.c_uint16),
    ("moreFrags", ctypes.c_uint16),
    ("retry", ctypes.c_uint16),
    ("powerMgmt", ctypes.c_uint16),
    ("more", ctypes.c_uint16),
    ("protect", ctypes.c_uint16),
    ("order", ctypes.c_uint16),
  ]


class LibpicoStandardHeader(ctypes.Structure):
  _pack_ = 1
  _fields_ = [
    ("controlField", Ieee80211MacFrameHeaderControlField),
    ("addr1", ctypes.c_uint8 * 6),
    ("addr2", ctypes.c_uint8 * 6),
    ("addr3", ctypes.c_uint8 * 6),
    ("frag", ctypes.c_uint16),
    ("seq", ctypes.c_uint16),
  ]


class LibpicoRxSBasic(ctypes.Structure):
  _pack_ = 1
  _fields_ = [
    ("deviceType", ctypes.c_uint16),
    ("tstamp", ctypes.c_uint64),
    ("systemTime", ctypes.c_uint64),
    ("centerFreq", ctypes.c_int16),
    ("controlFreq", ctypes.c_int16),
    ("cbw", ctypes.c_uint16),
    ("packetFormat", ctypes.c_uint8),
    ("pktCbw", ctypes.c_uint16),
    ("guardInterval", ctypes.c_uint16),
    ("mcs", ctypes.c_uint8),
    ("numSTS", ctypes.c_uint8),
    ("numESS", ctypes.c_uint8),
    ("numRx", ctypes.c_uint8),
    ("noiseFloor", ctypes.c_int8),
    ("rssi", ctypes.c_int8),
  ]


class LibpicoRxExtraInfo(ctypes.Structure):
  _pack_ = 1
  _fields_ = [
    ("featureCode", ctypes.c_uint32),
    ("length", ctypes.c_uint16),
    ("version", ctypes.c_uint64),
    ("macAddrRom", ctypes.c_uint8 * 6),
    ("macAddrCur", ctypes.c_uint8 * 6),
    ("channelSelect", ctypes.c_uint32),
    ("bmode", ctypes.c_uint8),
    ("evm", ctypes.c_int8 * 20),
    ("txChainMask", ctypes.c_uint8),
    ("rxChainMask", ctypes.c_uint8),
    ("txPower", ctypes.c_uint8),
    ("cf", ctypes.c_uint64),
    ("txTsf", ctypes.c_uint32),
    ("lastHwTxTsf", ctypes.c_uint32),
    ("channelFlags", ctypes.c_uint16),
    ("txNess", ctypes.c_uint8),
    ("tuningPolicy", ctypes.c_uint8),
    ("pllRate", ctypes.c_uint16),
    ("pllRefdiv", ctypes.c_uint8),
    ("pllClockSelect", ctypes.c_uint8),
    ("agc", ctypes.c_uint8),
    ("antSelect", ctypes.c_uint8 * 3),
    ("samplingRate", ctypes.c_uint64),
    ("cfo", ctypes.c_int32),
    ("sfo", ctypes.c_int32),
  ]


class LibpicoCsi(ctypes.Structure):
  _pack_ = 1
  _fields_ = [
    ("deviceType", ctypes.c_uint16),
    ("firmwareVersion", ctypes.c_uint8),
    ("packetFormat", ctypes.c_int8),
    ("cbw", ctypes.c_uint16),
    ("carrierFreq", ctypes.c_uint64),
    ("samplingRate", ctypes.c_uint64),
    ("subcarrierBandwidth", ctypes.c_uint32),
    ("antSelect", ctypes.c_uint8),
    ("subcarrierOffset", ctypes.c_int16),
    ("nTones", ctypes.c_uint16),
    ("nTx", ctypes.c_uint8),
    ("nRx", ctypes.c_uint8),
    ("nEss", ctypes.c_uint8),
    ("nCsi", ctypes.c_uint16),
    ("subcarrierIndicesPtr", ctypes.POINTER(ctypes.c_int16)),
    ("subcarrierIndicesSize", ctypes.c_int64),
    ("csiRealPtr", ctypes.POINTER(ctypes.c_float)),
    ("csiImagPtr", ctypes.POINTER(ctypes.c_float)),
    ("csiSize", ctypes.c_int64),
    ("magnitudePtr", ctypes.POINTER(ctypes.c_float)),
    ("magnitudeSize", ctypes.c_int64),
    ("phasePtr", ctypes.POINTER(ctypes.c_float)),
    ("phaseSize", ctypes.c_int64),
  ]


class LibpicoRaw(ctypes.Structure):
  _pack_ = 1
  _fields_ = [
    ("meta", LibpicoMeta),
    ("standardHeader", LibpicoStandardHeader),
    ("rxSBasic", LibpicoRxSBasic),
    ("rxExtraInfo", LibpicoRxExtraInfo),
    ("csi", LibpicoCsi),
  ]
