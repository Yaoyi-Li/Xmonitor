import socket
import struct
import time
import coloredLogger
import sys
from sysinfoCollector import sysinfo2JSON



HOST = 'localhost'
PORT = 8002   
REQUIRE = [
    'CPU-util',
    ''
]

# def socketSend(socket, data):
#     sent = 0
#     while sent < len(data):
#         sentOnce = socket.send(data[sent:])
#         if sentOnce == 0:
#             raise RuntimeError('Connection Broken')
#         sent += sentOnce
#     return sent




if __name__ == '__main__':


    logger = coloredLogger.getLogger('XmonitorClient')

    while True:

        # Catch the exception of loss connection
        try:

            while True:
                try:
                    # Connect to server and send data
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(10)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    logger.info('Connecting\t%s:%d' % (HOST, PORT))
                    sock.connect((HOST, PORT))
                    logger.info('Connect Successfully\t%s:%d' % (HOST, PORT))
                    break

                except KeyboardInterrupt:
                    raise

                except:
                    logger.error('Can\'t Reach\t%s:%d' % (HOST, PORT))
                    logger.info('Reconnect in 120 sec')
                    sock.close()
                    time.sleep(120)

            while True:
                msg = sysinfo2JSON(REQUIRE).encode()
            
                packedHdr = struct.pack('L', len(msg))

                # socketSend(sock, packedHdr)
                # socketSend(sock, msg)

                sock.sendall(packedHdr)
                sock.sendall(msg)


        except RuntimeError:
            logger.error('Loss Connection\t%s:%d' % (HOST, PORT))
            logger.info('Reconnect in 120 sec')
            sock.close()
            time.sleep(120)

        except KeyboardInterrupt:
            print('\nStop Client? (y/n)')
            checkStop = input('>>')

            if checkStop[0].upper() == 'Y':
                logger.info('Client Stopped')
                sock.close()
                sys.exit(0)
                
            else:
                logger.info('Reconnect \t%s:%d' % (HOST, PORT))

        except Exception as e:
            logger.error('FATAL ERROR\t' + str(e))
            import traceback
            traceback.print_exc()


