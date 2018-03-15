import json
import socketserver
import struct
import threading
import signal
import time
import coloredLogger
import sys
import os



HOST = ''
PORT = 7999
CACHE_DIR = '/dev/shm/XmonitorCache'



class JsonParser(object):

    jsonFileName = 'tmp.json'
    jsonCacheDir = '/dev/shm'
    jsonObj = {}
    jsonStr = ''

    def __init__(self, fileName=jsonFileName, cacheDir=jsonCacheDir):
        self.jsonFileName = fileName
        self.jsonCacheDir = cacheDir

    def parse(self, jsonData):
        self.jsonObj = jsonData
        self.jsonStr = json.dumps(self.jsonObj)
    
    def writeToCache(self):
        jsonPath = os.path.join(self.jsonCacheDir, self.jsonFileName)
        logger.debug('Write to Cache\t'+jsonPath)
        with open(jsonPath, 'w') as cache:
            cache.write(self.jsonStr)





class JsonServerHandler(socketserver.BaseRequestHandler):

    ip = '0.0.0.0'
    port = 0
    timeout = 5

    def _read(self, msgSize):
        data = b''
        bytes_record = 0
        logger.debug('message size: ' + str(msgSize))

        while len(data) < msgSize:
            dataBuf = self.request.recv(min(msgSize - bytes_record, 2048))

            if dataBuf == b'':
                logger.error('Connection Broken\t%s:%d' % (self.ip, self.port))
                raise RuntimeError('Connection Broken')
                
            data += dataBuf

        return data
    
    def _readMsgLength(self):
        headSize = struct.calcsize('L')
        head = self._read(headSize)
        msgSize = struct.unpack('L', head)[0]
        return msgSize

    def setup(self):
        self.ip = self.client_address[0].strip()
        self.port = self.client_address[1]
        logger.info('Connect Client\t%s:%d' % (self.ip, self.port))

    def handle(self):

        cacheName = self.ip.replace('.', '_') + '.json'
        jsonParser = JsonParser(cacheName, CACHE_DIR)

        while True:
            msgSize = self._readMsgLength()
            data = self._read(msgSize)
            jsonData = json.loads(data.decode())
            try:
                jsonParser.parse(jsonData)
            except:
                raises
            jsonParser.writeToCache()

            time.sleep(0.5)


    def finish(self):
        logger.warn('Disonnect Client\t%s:%d' % (self.ip, self.port))


class JsonServer(socketserver.ThreadingMixIn, socketserver.TCPServer):

    allow_reuse_address = True

    def handle_error(self, request, client_address):
        """Handle an error gracefully.  May be overridden.
        The default is to print a traceback and continue.
        """
        print('-'*40, file=sys.stderr)
        import traceback
        traceback.print_exc()
        print('-'*40, file=sys.stderr)


if __name__ == '__main__':

    logger = coloredLogger.getLogger('XmonitorServer')


    # Create cache dir
    if not os.path.isdir(CACHE_DIR):
        logger.info('Creating Cache DIR\t' + CACHE_DIR)
        os.mkdir(CACHE_DIR)
    else:
        files = os.listdir(CACHE_DIR)
        for item in files:
            itemPath = os.path.join(CACHE_DIR,item)
            try:
                os.remove(itemPath)
            except:
                logger.warn('Can\'t Remove ' + itemPath)
                pass

    
    server = JsonServer((HOST, PORT), JsonServerHandler)
    with server:
        server_thread = threading.Thread(target=server.serve_forever)

        server_thread.daemon = True
        logger.info('Server Starting')
        server_thread.start()
        logger.info('Server Listening on PORT: %d' %(PORT) )

        while True:
            try:
                signal.pause()
                
            except:
                print('\nStop Server? (y/n)')
                checkStop = input('>>')

                if checkStop[0].upper() == 'Y':
                    logger.info('Server Stopped')
                    server.shutdown()
                    break
