#from imutils.video import VideoStream
from flask import Response
from flask import Flask
from multiprocessing import Process, Array
import argparse
from datetime import datetime
import cv2
import numpy as np
import ctypes
from threading import Thread
import time
import vonage
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import socket


client = vonage.Client(key="68184f1d", secret="NeXPMFdDSugGz1v7")
sms = vonage.Sms(client)

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://survelliance-camera-77550-default-rtdb.europe-west1.firebasedatabase.app/"
})

ref = db.reference("ips")

SCREEN_HEIGHT = 600
SCREEN_WIDTH = 800

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


outputFrame = []
avail_cams = []

def getVideo(camURL, camID):
    stream = cv2.VideoCapture(camURL)
    stream.set(cv2.CAP_PROP_FPS, 30)
    stream.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
    stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)
    oldTime = -300
    old_frame = None
    first = True
    while 1:
        _, frame = stream.read()
        if frame is None:
            continue
        timestamp = datetime.now()
        cv2.putText(frame, timestamp.strftime("%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0] -10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
        
        outputFrame[camID][:] = frame
        
        gray_frame=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        gray_frame=cv2.GaussianBlur(gray_frame,(25,25),0)
        
        # First frame will be none therefore we need to set it to the current frame
        if old_frame is None:
            old_frame = gray_frame

        delta=cv2.absdiff(old_frame,gray_frame)
        old_frame = gray_frame
        threshold=cv2.threshold(delta,35,255, cv2.THRESH_BINARY)[1]

        (contours,_)=cv2.findContours(threshold,cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            if cv2.contourArea(contour) < 5000:
                # More than 5minutes between each motion notification
                if time.time() - oldTime > 300 and not first:
                    oldTime = time.time()
                    # UNCOMMENT THIS FOR PRODUCTION
                    # Generate a sms notification

                    # responseData = sms.send_message(
                    # {
                    #     "from": "Camera",
                    #     "to": "46763235353",
                    #     "text": f"Motion detected on camera {camID}",
                    # }
                    # )

                    # if responseData["messages"][0]["status"] == "0":
                    #     print("Message sent successfully.")
                    # else:
                    #     print(f"Message failed with error: {responseData['messages'][0]['error-text']}")
                    print(f"detected motion on cam {camID}")
                first = False
                continue    

def generate_feed(camID):
    while 1:
        #frame = outputFrame
        
        #(flag, encodedImage) = cv2.imencode(".jpg", frame)
        #print(type(encodedImage))
        #if not flag:
            
         #    continue
        # yield the output frame in the byte format
        # yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
        #     bytearray(encodedImage) + b'\r\n')
        
        # Encode the raw video
        yield (b'--frame\r\n'
            # b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n\r\n')
            b'Content-Type: image/jpeg\r\n\r\n' + cv2.imencode('.jpg', outputFrame[camID])[1].tobytes() + b'\r\n\r\n')


@app.route('/video_feed/<int:cam>')
def video_feed(cam):
    # Return the video stream
    return Response(generate_feed(cam),
            mimetype = "multipart/x-mixed-replace; boundary=frame")

@app.route("/available_cams")
def available_cams():
	return avail_cams

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--ip", type=str, required=True,
        help="ip address of the device")
    ap.add_argument("-o", "--port", type=int, required=True,
        help="ephemeral port number of the server (1024 to 65535)")
    ap.add_argument("-f", "--frame-count", type=int, default=32,
        help="# of frames used to construct the background model")

    args = vars(ap.parse_args())
    
    #hostname=socket.gethostname()   
    IPAddr="10.22.5.251" #socket.gethostbyname(hostname)  

    cams = ref.get()
    #cams = [0, "rtsp://192.168.1.68:8554/mjpeg/1"]
    print(cams)
    for i, cam in enumerate(cams):
        # append default frame ; black screen
        if cam == 0: outputFrame.append(np.ctypeslib.as_array(Array(ctypes.c_uint8, 480 * 848 * 3).get_obj()).reshape(480, 848, 3))
        else : outputFrame.append(np.ctypeslib.as_array(Array(ctypes.c_uint8, SCREEN_HEIGHT * SCREEN_WIDTH * 3).get_obj()).reshape(SCREEN_HEIGHT, SCREEN_WIDTH, 3))
        
        frontendRef = db.reference(f"cameras/{i}/ip")
        frontendRef.set(IPAddr+f":5000/video_feed/{i}")
        print(IPAddr)
        # append to available cams array
        avail_cams.append(i)
        
        # start a process for every video 
        Process(target=getVideo, args=(cam, i)).start()
    
    #start flask app
    thread_flask = Thread(app.run(host=args["ip"], port=args["port"], debug=True, threaded=True, use_reloader=False))
    thread_flask.daemon = True
    thread_flask.start()    