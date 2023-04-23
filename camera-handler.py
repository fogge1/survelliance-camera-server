from imutils.video import VideoStream
from flask import Response
from flask import Flask
import imutils
from multiprocessing import Process, Array
import argparse
from datetime import datetime
import cv2
import numpy as np
import ctypes
from threading import Thread

SCREEN_HEIGHT = 300
SCREEN_WIDTH = 400

app = Flask(__name__)
# class videoStream (threading.Thread):
#     def __init__(self, threadID, name, videoUrl):
#         threading.Thread.__init__(self)
#         self.threadID = threadID
#         self.name = name
#         self.videoUrl = videoUrl
#     def run(self):
#         vs = VideoStream(src=self.videoUrl).start()
#         getVideo(vs, self.threadID)

outputFrames = []

def getVideo(name, camURL, output):
    
    vs = VideoStream(src=camURL).start()
    frame = None
    old_frame = None
    while 1:
        frame = vs.read()
        frame = imutils.resize(frame, width=400)
        #timestamp = datetime.now()
        #cv2.putText(frame, timestamp.strftime("%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0] -10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
        
        output[:] = frame.copy()

        gray_frame=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        gray_frame=cv2.GaussianBlur(gray_frame,(25,25),0)
        
        if old_frame is None:
            old_frame = gray_frame

        delta=cv2.absdiff(old_frame,gray_frame)
        old_frame = gray_frame
        threshold=cv2.threshold(delta,35,255, cv2.THRESH_BINARY)[1]

        (contours,_)=cv2.findContours(threshold,cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            if cv2.contourArea(contour) < 5000:
                #print(f"detected motion on cam {name}")
                continue    

def generate_feed(camID):
    while 1:
        frame = outputFrames[camID]
        
        (flag, encodedImage) = cv2.imencode(".jpg", frame)
        if not flag:
            
            continue
        # yield the output frame in the byte format
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
            bytearray(encodedImage) + b'\r\n')

@app.route('/video_feed/<int:cam>')
def video_feed(cam):
    return Response(generate_feed(cam),
            mimetype = "multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--ip", type=str, required=True,
        help="ip address of the device")
    ap.add_argument("-o", "--port", type=int, required=True,
        help="ephemeral port number of the server (1024 to 65535)")
    ap.add_argument("-f", "--frame-count", type=int, default=32,
        help="# of frames used to construct the background model")

    args = vars(ap.parse_args())

    # thread1 = videoStream(0, "Thread-0", 0)
    # outputFrames.append(None)
    # thread1.start()
    # thread2 = videoStream(1, "Thread-1", "rtsp://192.168.1.68:8554/mjpeg/1")
    # outputFrames.append(None)
    # thread2.start()
    outputFrames = [np.ctypeslib.as_array(Array(ctypes.c_uint8, SCREEN_HEIGHT * SCREEN_WIDTH * 3).get_obj()).reshape(SCREEN_HEIGHT, SCREEN_WIDTH, 3)]
    Process(target=getVideo, args=("webcam",0, outputFrames[0])).start()
    # l = Process(target=getVideo, args=("esp", "rtsp://192.168.1.68:8554/mjpeg/1",))
    # l.start()
    #start flask app
    thread_flask = Thread(app.run(host=args["ip"], port=args["port"], debug=True, threaded=True, use_reloader=False))
    thread_flask.daemon = True
    thread_flask.start()