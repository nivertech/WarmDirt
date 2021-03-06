#!/usr/bin/env python

import serial
import os,sys
import sys
import termios
import socket
import mosquitto, time
import traceback

PORT=7764

import BaseHTTPServer, SimpleHTTPServer, cgi


ser = serial.Serial('/dev/ttyUSB0', 57600,timeout=1)

class ReqHandler (SimpleHTTPServer.SimpleHTTPRequestHandler) :
    def do_GET(self) :
        if self.path=='/light=on':
            self.send_response(204)
            self.end_headers()
            ser.write("a11s")
            return
        elif self.path=='/light=off':
            ser.write("a10s")
            self.send_response(204)
            #self.send_header('Content-type','text/html')
            self.end_headers()
            return
        else:
            SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

http = BaseHTTPServer.HTTPServer(('',PORT),ReqHandler)
print 'http port=%d'%PORT
http.socket.settimeout(0.1)

def on_connect(rc):
    if rc == 0:
        print "mqtt connected successfully."
        ser.write("s")
    else:
        print "mqtt onnected unsuccessfully."

print "console.py"

def getchar():
    fd = sys.stdin.fileno()

    if os.isatty(fd):
        old = termios.tcgetattr(fd)
        new = termios.tcgetattr(fd)
        new[3] = new[3] & ~termios.ICANON & ~termios.ECHO
        new[6] [termios.VMIN] = 0
        new[6] [termios.VTIME] = 0

        try:
            termios.tcsetattr(fd, termios.TCSANOW, new)
            termios.tcsendbreak(fd,0)
            ch = os.read(fd,7)

        finally:
            termios.tcsetattr(fd, termios.TCSAFLUSH, old)
    else:
        ch = os.read(fd,7)

    return(ch)



while True:
    mqtt = mosquitto.Mosquitto("warmdirt")
    mqtt.connect("localhost")
    mqtt.on_connect = on_connect

    sum = 0
    line = ""
    len  = -9999 #
    while True:
        if ser.inWaiting():
            c = ser.read()
            u = ord(c)
            if u == 2:
                sum = 0
                line = ""
                len = 9999 # startup condition
            else:
#                if u > 29 and u < 123:
#                    print "%-4d %-4d %c"%(len,u,c)
#                else:
#                    print "%-4d %-4d   "%(len,u)

                if len == 9999:
                    len = u
                if len == -2:
                    if (sum&0xff) == 0:
                        #print "/%c%s"%(line[1],line[3:-1])
                        try:
                            (k,v) = line[3:-1].split("=")
                            k = "us/co/montrose/1001s2nd/warmdirt/%c%s"%(line[1],k)
                            mqtt.publish(k,v, qos=0, retain=False)
                            if k.count("uptime"):
                                print
                            print time.strftime("%m-%d-%Y %H:%M:%S", time.localtime(time.time())),
                            print "%-30s %s"%(k[33:],v)
                        except:
                            print line
                            traceback.print_exc(file=sys.stdout)
                else:
                    sum += u
                    line += c
                len  -= 1
        else:
            http.handle_request()
        if mqtt.loop(0) != 0:
            break
        c = getchar()
        if c:
            ser.write(c)
    mqtt.disconnect()
    print "sleeping for 10"
    time.sleep(10)
