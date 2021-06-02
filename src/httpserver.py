'''
Created on Nov 16, 2020

@author: ashley burke
'''

import sys
import argparse
import socket
import time
import threading
import os

def sendWebPage(connSend, file2send, ver, loc):
    try:
        with open(file2send,'r') as htmlfile:
            connSend.sendall(str.encode(ver + ' 200 OK\n'))
            connSend.sendall(str.encode('Content-Type: text/html\n'))
            connSend.sendall(str.encode('\n')) # header and body should be separated by additional newline
            for line in htmlfile:
                connSend.send(str.encode(line))
                
        sys.stderr.write('Success: served file ' + loc[1:] + '\n')
        
    except FileNotFoundError:
        ver10 = 'HTTP/1.0 404 NOT FOUND\n'
        ver11 = 'HTTP/1.1 404 NOT FOUND\n'
        
        if ver == 'HTTP/1.0' :
            sys.stderr.write(ver10)
            connSend.sendall(str.encode(ver10))
            return
        if ver == 'HTTP/1.1' :
            sys.stderr.write(ver11)
            connSend.sendall(str.encode(ver11))
            return
    
    connSend.close()
    
def threaded_client(threadConn, to, base_directory):

    try:
        conn.settimeout(to)
    
        time_delay = 0
        data = conn.recv(2048).decode()
#         data = data[:len(data) - 1] #Gets rid of the \n from inputting the data

        fields = data.split('\r\n')
        
        request_line = fields[0]
        
        request_line_parsed = request_line.split(' ')
        
        #Invalid character encoding (non-ASCII characters in input): 
        if data.isascii() == False:
            sys.stderr.write('Error: invalid input character\n')
            threadConn.close()
            return
            
        if len(request_line_parsed) == 3:
            method = request_line_parsed[0]
            location = request_line_parsed[1]
            version = request_line_parsed[2]
            
#             End of data while waiting for more input:
            if data.count('\r\n\r\n') == 0 :
                sys.stderr.write('Error: unexpected end of input\n')
                threadConn.close()
                return
 
            #Incorrectly formatted request line (method other than GET, unknown HTTP version, etc.):
            if (method != 'GET') or (version != 'HTTP/1.1' and version != 'HTTP/1.0' ):
                sys.stderr.write('Error: invalid request line\n')
                threadConn.close()
                return
  
            if len(fields) > 1 :
                header_lines = fields[0:]

                for header in header_lines :
                    if header.count('X-additional-wait: ') == 1 :
                        time_delay = int(header[19:])
                        
                time.sleep(time_delay)
            
            #Malformed or non-existing file path:
            #checks to see if the input directory contains a back reference for directory traversal
            if location.count('../') != 0:
                sys.stderr.write('Error: invalid path\n')
                msg = version + ' 404 NOT FOUND\r\n\r\n'
                threadConn.send(str.encode(msg))
                threadConn.close()
                return
            
            #Malformed or non-existing file path:
            last_dir = location.rindex("/")
            given_directory = location[:last_dir+1]
            total_dir = base_directory + given_directory
            if os.path.isdir(total_dir) == False:
                sys.stderr.write('Error: invalid path\n')
                msg = version + ' 404 NOT FOUND\r\n\r\n'
                threadConn.send(str.encode(msg))
                threadConn.close()
                threadConn.close()
                return
          
        else:
            sys.stderr.write('Error: invalid request line\n')
            threadConn.close()
            return
        
        filename = base_directory + location   
        sendWebPage(conn, filename, version, location)
        threadConn.close()
    
    except Exception:
            sys.stderr.write('Error: socket recv timed out\n')
            threadConn.close()
            return
   

if __name__ == '__main__':
    
    directory = '/Users/ashley/Desktop/School'
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', help=" --port : port on which the HTTP server should listen for connections. Default 8080", default=8080, type=int)
    parser.add_argument('--maxrq', help="--maxrq <# REQUESTS>: maximum number of concurrent requests. Default - 10", default=10, type=int)
    parser.add_argument('--timeout', help="--timeout : maximum number of seconds to wait for a client. Default - 10", default=10, type=int)
    args = parser.parse_args()

    listenerHost = '127.0.0.1'     
    listenerPort = args.port
        
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    
    try: 
        # binding listenerHost and listenerPort 
        serverSocket.bind((listenerHost, listenerPort)) 
           
    except socket.error as massage: 
        # program closes if bind fails
        print('Bind failed. Error Code : ' 
              + str(massage[0]) + ' Message ' 
              + massage[1]) 
        sys.exit() 
          
    
    
    # Sets number of concurrent sessions to args.maxrq
    serverSocket.listen(args.maxrq) 
           
    while True:
        try:
            conn, address = serverSocket.accept() 
            try:
                # print the address of connection 
                sys.stderr.write('Information: received new connection from ' + address[0] + ', port ' + str(address[1]) + '\n')
                threading._start_new_thread(threaded_client,(conn,args.timeout, directory))
            except Exception as err:
                sys.stderr.write('Thread Connection Error:', err)
                pass
        except Exception as err:
            sys.stderr.write('Socket Connection Error:', err)
            pass