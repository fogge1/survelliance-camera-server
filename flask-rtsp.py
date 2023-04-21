from imutils.video import VideoStream
from flask import Response
from flask import Flask
from flask import render_template
import threading
import argparse
import datetime
import imutils
import time
import cv2

import firebase_admin

from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://survelliance-camera-77550-default-rtdb.europe-west1.firebasedatabase.app/"
})

ref = db.reference('ips')

URL = ref.get()
print(URL)
app = Flask(__name__)
lock = threading.Lock()

# time.sleep(2.0)

def generate_video(vs):
	counter = 0
	frame = None
	while 1:

		frame = vs.read()
		print(counter)
		counter += 1

		frame = imutils.resize(frame, width=400)
		timestamp = datetime.datetime.now()

		cv2.putText(frame, timestamp.strftime("%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0] -10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
		with lock:
			if frame is None:
				continue
			(flag, encodedImage) = cv2.imencode(".jpg", frame)

			if not flag:
				continue
			yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
			bytearray(encodedImage) + b'\r\n')

@app.route("/video_feed/<page>")
def video_feed(page):

	vs = VideoStream(src=ref.get()[page]).start()
	# return the response generated along with the specific media
	# type (mime type)
	return Response(generate_video(vs),
		mimetype = "multipart/x-mixed-replace; boundary=frame")

if __name__ == '__main__':
	# construct the argument parser and parse command line arguments
	ap = argparse.ArgumentParser()
	ap.add_argument("-i", "--ip", type=str, required=True,
		help="ip address of the device")
	ap.add_argument("-o", "--port", type=int, required=True,
		help="ephemeral port number of the server (1024 to 65535)")
	ap.add_argument("-f", "--frame-count", type=int, default=32,
		help="# of frames used to construct the background model")
	args = vars(ap.parse_args())
	# start a thread that will perform motion detection
	
	# start the flask app
	app.run(host=args["ip"], port=args["port"], debug=True,
		threaded=True, use_reloader=False)
# release the video stream pointer