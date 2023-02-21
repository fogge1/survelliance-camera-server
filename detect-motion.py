import cv2
import random
import time

vcap = cv2.VideoCapture("rtsp://localhost:8554/test")

def detectedMotion():
    print("motion" + str(random.randint(1, 2000)))

oldTime = 0
newTime = 0
old_frame = None

while 1:
    ret, frame = vcap.read()
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
            newTime = time.perf_counter()
            if newTime - oldTime > 5:
                oldTime = time.perf_counter()
                detectedMotion()
            continue
        (x, y, w, h)=cv2.boundingRect(contour)
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 1)

    cv2.imshow('VIDEO', frame)
    cv2.waitKey(1)