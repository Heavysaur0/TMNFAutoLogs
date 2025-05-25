import struct


class GBXBaseFetcher:
    # Supported class IDs
    GBX_CHALLENGE_TMF = 0x03043000
    GBX_AUTOSAVE_TMF  = 0x03093000
    GBX_CHALLENGE_TM  = 0x24003000
    GBX_AUTOSAVE_TM   = 0x2403F000
    GBX_REPLAY_TM     = 0x2407E000

    MACHINE_ENDIAN_ORDER = 0
    LITTLE_ENDIAN_ORDER  = 1
    BIG_ENDIAN_ORDER     = 2

    LOAD_LIMIT = 1024  # KBs

    def __init__(self, parse_xml=False, debug=False):
        self.parse_xml = parse_xml
        self.xml = ''
        self.xmlParsed = {}

        self.author_ver = 0
        self.author_login = ''
        self.author_nick = ''
        self.author_zone = ''
        self.author_einfo = ''

        self._gbxdata = b''
        self._gbxlen = 0
        self._gbxptr = 0
        self._debug = debug
        self._error = ''
        self._lookbacks = None
        self._parsestack = []

        # Determine machine endianess
        self._endianess = self.LITTLE_ENDIAN_ORDER if struct.unpack('<L', struct.pack('=L', 1))[0] == 1 else self.BIG_ENDIAN_ORDER

    # Debugging methods
    def enableDebug(self):
        self._debug = True

    def disable_debug(self):
        self._debug = False

    def debugLog(self, msg):
        if self._debug:
            print(msg)

    # Error handling
    def setError(self, prefix):
        self._error = str(prefix)

    def error_out(self, msg, code=0):
        self.clear_gbxdata()
        raise Exception(f"{self._error}{msg}", code)

    # Load/store GBX data
    def loadGBXdata(self, filename):
        try:
            with open(filename, 'rb') as f:
                self.storeGBXdata(f.read(self.LOAD_LIMIT * 1024))
        except IOError:
            self.error_out(f"Unable to read GBX data from {filename}", 1)

    def storeGBXdata(self, gbxdata: bytes):
        self._gbxdata = gbxdata
        self._gbxlen = len(gbxdata)
        self._gbxptr = 0
        if self._gbxlen > 0:
            self.debugLog(f"GBX data length: {self._gbxlen}")

    def retrieveGBXdata(self):
        return self._gbxdata

    def clearGBXdata(self):
        self.storeGBXdata(b'')

    # Pointer helpers
    def getGBXptr(self):
        return self._gbxptr

    def setGBXptr(self, ptr):
        self._gbxptr = int(ptr)

    def moveGBXptr(self, length):
        self._gbxptr += int(length)

    # Data reading
    def readData(self, length):
        if self._gbxptr + length > self._gbxlen:
            self.error_out(f"Insufficient data for {length} bytes at pos 0x{self._gbxptr:04X}", 2)
        data = self._gbxdata[self._gbxptr:self._gbxptr + length]
        self._gbxptr += length
        return data

    def readInt8(self):
        return struct.unpack('b', self.readData(1))[0]

    def readInt16(self):
        fmt = '>h' if self._endianess == self.BIG_ENDIAN_ORDER else '<h'
        return struct.unpack(fmt, self.readData(2))[0]

    def readInt32(self):
        fmt = '>l' if self._endianess == self.BIG_ENDIAN_ORDER else '<l'
        return struct.unpack(fmt, self.readData(4))[0]
    
    def readString(self):
        len_ = self.readInt32() & 0x7FFFFFFF
        if len_ <= 0 or len_ >= 0x18000:
            if len_ != 0:
                self.errorOut(f'Invalid string length {len_} (0x{len_:04X}) at pos 0x{self.getGBXptr():04X}', 3)
        data = self.readData(len_)
        return data.decode('utf-8', errors='replace')

    def stripBOM(self, s):
        return s.replace('\xef\xbb\xbf', '')

    def clearLookbacks(self):
        self._lookbacks = None

    def readLookbackString(self):
        if self._lookbacks is None:
            self._lookbacks = []
            version = self.readInt32()
            if version != 3:
                self.errorOut(f'Unknown lookback strings version: {version}', 4)

        index = self.readInt32()
        if index == -1:
            return ''
        elif (index & 0xC0000000) == 0:
            return {
                11: 'Valley',
                12: 'Canyon',
                13: 'Lagoon',
                17: 'TMCommon',
                26: 'Stadium',
                202: 'Storm',
                299: 'SMCommon',
                10003: 'Common'
            }.get(index, 'UNKNOWN')
        elif (index & 0x3FFFFFFF) == 0:
            s = self.readString()
            self._lookbacks.append(s)
            return s
        else:
            return self._lookbacks[(index & 0x3FFFFFFF) - 1]

    # XML Parsing
    def startTag(self, name, attribs):
        attribs = {k: v.encode('utf-8').decode('utf-8') for k, v in attribs.items()}
        self._parsestack.append(name)
        if name == 'DEP':
            self.xmlParsed.setdefault('DEPS', []).append(attribs)
        elif len(self._parsestack) <= 2:
            self.xmlParsed[name] = attribs

    def charData(self, data):
        if len(self._parsestack) == 3:
            self.xmlParsed[self._parsestack[1]][self._parsestack[2]] = data
        elif len(self._parsestack) > 3:
            self.debugLog(f"XML chunk nested too deeply: {self._parsestack}")

    def endTag(self, name):
        self._parsestack.pop()

    def parseXMLstring(self):
        parser = xml.parsers.expat.ParserCreate()
        parser.StartElementHandler = self.startTag
        parser.EndElementHandler = self.endTag
        parser.CharacterDataHandler = self.charData

        # Escape bare '&' characters
        xml = self.xml
        xml = xml.replace('&', '&amp;') if '&' in xml and not any(ent in xml for ent in ['&amp;', '&quot;', '&apos;', '&lt;', '&gt;']) else xml

        try:
            parser.Parse(xml.encode('utf-8'), True)
        except xml.parsers.expat.ExpatError as e:
            self.errorOut(f"XML chunk parse error: {e} at line {parser.ErrorLineNumber}", 12)

    def checkHeader(self, classes):
        data = self.readData(3)
        version = self.readInt16()
        if data != b'GBX':
            self.errorOut('No magic GBX header', 5)
        if version != 6:
            self.errorOut(f'Unsupported GBX version: {version}', 6)

        self.moveGBXptr(4)  # Skip unknown/format/compression

        mainClass = self.readInt32()
        if mainClass not in classes:
            self.errorOut(f'Main class ID {mainClass:08X} not supported', 7)
        self.debugLog(f'GBX main class ID: {mainClass:08X} - {self._gbxptr}')

        headerSize = self.readInt32()
        self.debugLog(f'GBX header block size: {headerSize} ({headerSize / 1024:.1f} KB) - {self._gbxptr}')
        return headerSize

    def getChunksList(self, header_size: int, chunks: dict) -> dict:
        num_chunks = self.readInt32()
        if num_chunks == 0:
            self.error_out('No GBX header chunks', 9)

        self.debugLog(f'GBX number of header chunks: {num_chunks} - {self._gbxptr}')
        chunk_start = self.getGBXptr()
        self.debugLog(f'GBX start of chunk list: 0x{chunk_start:04X}')
        chunk_offset = chunk_start + num_chunks * 8

        chunks_list = {}
        for i in range(num_chunks):
            chunk_id = self.readInt32()
            chunk_size = self.readInt32() & 0x7FFFFFFF

            name = chunks.get(chunk_id, 'UNKNOWN')
            if name != 'UNKNOWN':
                chunks_list[name] = {
                    'off': chunk_offset,
                    'size': chunk_size
                }

            self.debugLog(f'GBX chunk {i:2d}  {name:<8}  Id  0x{chunk_id:08X}  Offset  0x{chunk_offset:06X}  Size {chunk_size:6d}')
            chunk_offset += chunk_size

        total_size = chunk_offset - chunk_start + 4
        if header_size != total_size:
            self.error_out(f'Chunk list size mismatch: {header_size} <> {total_size}', 10)

        return chunks_list


    def initChunk(self, offset: int):
        self.setGBXptr(offset)
        self.clearLookbacks()


    def getXMLChunk(self, chunks_list: dict):
        if 'XML' not in chunks_list:
            return

        self.initChunk(chunks_list['XML']['off'])
        self.xml = self.readString()
        xml_len = len(self.xml)

        if xml_len > 0 and chunks_list['XML']['size'] != xml_len + 4:
            self.error_out(f'XML chunk size mismatch: {chunks_list["XML"]["size"]} <> {xml_len + 4}', 11)

        if self.parse_xml and self.xml:
            self.parse_xml_string()


    def get_author_fields(self):
        self.author_ver = self.readInt32()
        self.author_login = self.readString()
        self.author_nick = self.strip_bom(self.readString())
        self.author_zone = self.strip_bom(self.readString())
        self.author_einfo = self.readString()


    def getAuthorChunk(self, chunks_list: dict):
        if 'Author' not in chunks_list:
            return

        self.init_chunk(chunks_list['Author']['off'])
        version = self.readInt32()
        self.debugLog(f'GBX Author chunk version: {version}')

        self.get_author_fields()

    def readFiletime(self):
        EPOCH_DIFF = 116444735995904000  # 100ns intervals between 1601-01-01 and 1970-01-01
        USEC2SEC = 1000000

        lo = self.readInt32()
        hi = self.readInt32()

        # 64-bit platforms
        if lo < 0:
            lo += 1 << 32
        if hi < 0:
            hi += 1 << 32

        filetime = (hi << 32) | lo

        self.debugLog(f'PAK CreationDate source: {filetime:016x}')

        if filetime == 0:
            return -1

        # Convert 100-nanosecond intervals to microseconds
        timestamp_usec = (filetime - EPOCH_DIFF) // 10
        timestamp_sec = timestamp_usec // USEC2SEC

        self.debugLog(f'PAK CreationDate 64-bit: {timestamp_sec}.{timestamp_usec % USEC2SEC:06d}')
        return timestamp_sec


class GBXReplayFetcher(GBXBaseFetcher):
    def __init__(self, parsexml=False, debug=False):
        super().__init__()

        self.uid = ''
        self.envir = ''
        self.author = ''
        self.replay = 0
        self.nickname = ''
        self.login = ''
        self.titleUid = ''

        self.xmlVer = ''
        self.exeVer = ''
        self.exeBld = ''
        self.respawns = 0
        self.stuntScore = 0
        self.validable = False
        self.cpsCur = 0
        self.cpsLap = 0
        self.vehicle = ''

        self.parseXml = bool(parsexml)
        if debug:
            self.enableDebug()

        self.setError('GBX replay error: ')

    def processFile(self, filename: str):
        self.loadGBXdata(str(filename))
        self.processGBX()

    def processData(self, gbxdata: str):
        self.storeGBXdata(str(gbxdata))
        self.processGBX()

    def processGBX(self):
        replayclasses = [
            self.GBX_AUTOSAVE_TMF,
            self.GBX_AUTOSAVE_TM,
            self.GBX_REPLAY_TM
        ]

        headerSize = self.checkHeader(replayclasses)
        if headerSize == 0:
            self.errorOut('No GBX header block', 8)

        headerStart = headerEnd = self.getGBXptr()

        chunks = {
            0x03093000: 'String',
            0x2403F000: 'String',
            0x03093001: 'XML',
            0x2403F001: 'XML',
            0x03093002: 'Author'
        }

        chunksList = self.getChunksList(headerSize, chunks)

        self.getStringChunk(chunksList)
        headerEnd = max(headerEnd, self.getGBXptr())

        self.getXMLChunk(chunksList)
        headerEnd = max(headerEnd, self.getGBXptr())

        self.getAuthorChunk(chunksList)
        headerEnd = max(headerEnd, self.getGBXptr())

        if headerSize != headerEnd - headerStart:
            self.errorOut(f'Header size mismatch: {headerSize} <> {headerEnd - headerStart}', 20)

        if self.parseXml:
            self.debugLog(f"xmlParsed -\n{self.xmlParsed}")
            x = self.xmlParsed
            if 'HEADER' in x:
                self.xmlVer = x['HEADER'].get('VERSION', '')
                self.exeVer = x['HEADER'].get('EXEVER', '')
                self.exeBld = x['HEADER'].get('EXEBUILD', '')
            if 'TIMES' in x:
                self.respawns = int(x['TIMES'].get('RESPAWNS', 0))
                self.stuntScore = int(x['TIMES'].get('STUNTSCORE', 0))
                self.validable = bool(x['TIMES'].get('VALIDABLE', False))
            if 'CHECKPOINTS' in x:
                self.cpsCur = int(x['CHECKPOINTS'].get('CUR', 0))
                self.cpsLap = int(x['CHECKPOINTS'].get('ONELAP', 0))
            if 'PLAYERMODEL' in x:
                self.vehicle = x['PLAYERMODEL'].get('ID', '')

        self.clearGBXdata()
        self.debugLog("")
        
    def getStringChunk(self, chunksList):
        if 'String' not in chunksList:
            return

        self.initChunk(chunksList['String']['off'])
        version = self.readInt32()
        self.debugLog(f'GBX String chunk version: {version}')

        if version >= 3:
            self.uid = self.readLookbackString()
            self.envir = self.readLookbackString()
            self.author = self.readLookbackString()
            self.replay = self.readInt32()
            self.nickname = self.stripBOM(self.readString())

            if version >= 6:
                self.login = self.readString()

                if version >= 8:
                    self.moveGBXptr(1)  # skip byte
                    self.titleUid = self.readLookbackString()


def gbx_replay_to_dict(fetcher):
    """
    Convert a GBXReplayFetcher instance into a dictionary with all metadata.

    Args:
        fetcher: An instance of a GBXReplayFetcher-like class.

    Returns:
        dict: Dictionary containing replay metadata.
    """
    return {
        'uid': fetcher.uid,
        'envir': fetcher.envir,
        'author': fetcher.author,
        'replay': fetcher.replay,
        'nickname': fetcher.nickname,
        'login': fetcher.login,
        'titleUid': fetcher.titleUid,
        'xmlVer': fetcher.xmlVer,
        'exeVer': fetcher.exeVer,
        'exeBld': fetcher.exeBld,
        'respawns': fetcher.respawns,
        'stuntScore': fetcher.stuntScore,
        'validable': fetcher.validable,
        'cpsCur': fetcher.cpsCur,
        'cpsLap': fetcher.cpsLap,
        'vehicle': fetcher.vehicle
    }

if __name__ == '__main__':
    replay_folder = "C:\\Users\\Cosmo\\Documents\\TrackMania\\Tracks\\Replays\\"
    replay1 = replay_folder + "A01-Race_HeavySωØur(01'17''93).Replay.Gbx"
    replay2 = replay_folder + "Downloaded\\[rpg] run Forrest run_ _ «(02'57''44).Replay.Gbx"
    gbx_replay_fetcher = GBXReplayFetcher(True, True)

    gbx_replay_fetcher.processFile(replay2)
    info = gbx_replay_to_dict(gbx_replay_fetcher)
    for key, value in info.items():
        print(f"{key} - {value}")
