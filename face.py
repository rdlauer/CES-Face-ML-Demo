#!/usr/bin/python3
import notecard
from notecard import hub
from periphery import I2C
import cv2
import keys
import time

# init the notecard
productUID = keys.NOTEHUB_PRODUCT_UID
port = I2C("/dev/i2c-1")
nCard = notecard.OpenI2C(port, 0, 0)

# connect notecard to notehub
rsp = hub.set(nCard, product=productUID, mode="continuous", sync=True)
print(rsp)

# create note template
req = {"req": "note.template"}
req["file"] = "face.qo"
req["body"] = {"face_count": 11, "voltage": 12.1, "temperature": 12.1}
rsp = nCard.Transaction(req)

# load the cascade
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# capture video from the pi camera 
cap = cv2.VideoCapture(0)

# keep track of face counts between notes
face_count = 0

# keep track of seconds for adding faces/syncing
start_secs_face = int(round(time.time()))
start_secs_note = int(round(time.time()))

def send_note(c):
    
    # query the notecard for voltage
    req = {"req": "card.voltage", "mode": "?"}
    rsp = nCard.Transaction(req)
    voltage = rsp["value"]
    
    # query the notecard for temp
    req = {"req": "card.temp"}
    rsp = nCard.Transaction(req)
    temperature = rsp["value"]

    req = {"req": "note.add"}
    req["file"] = "face.qo"
    req["body"] = {"face_count": c, "voltage": voltage, "temperature": temperature}
    req["sync"] = True
    rsp = nCard.Transaction(req)

    print(rsp)


while True:
    # track the current time
    current_seconds = int(round(time.time()))
    # Read the frame
    _, img = cap.read()
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Detect the faces
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    # Add text around each face
    font = cv2.FONT_HERSHEY_DUPLEX
    fontScale = 1
    color = (0, 0, 255)
    thickness = 2
    # Draw the rectangle around each face
    for (x, y, w, h) in faces:
        cv2.rectangle(img, (x, y), (x+w, y+h), color, 2)
        face_plural = 's'
        if face_count is 1:
            face_plural = ''
        cv2.putText(img, str(face_count) + ' face' + face_plural + ' found!', (x, y-10), font, 
                   fontScale, color, thickness, cv2.LINE_AA)
        
    # Display in window
    cv2.namedWindow('win', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('win', 900, 700)
    cv2.imshow('win', img)
    
    if len(faces) > 0:
        # check to make sure it's been at least three seconds since the last time we checked for faces
        if current_seconds - start_secs_face >= 3:
            face_count += len(faces)
            print("We found some faces: " + str(len(faces)) + " to be exact! (Pending sync: " + str(face_count) + " faces)")
            start_secs_face = int(round(time.time()))
    
    # create an outbound note every 5 minutes with accumulated face counts
    if current_seconds - start_secs_note >= 60:
        send_note(face_count)
        print("####################")
        print("Sending a new note with " + str(face_count) + " faces.")
        print("####################")
        face_count = 0
        start_secs_note = int(round(time.time()))
    
    # Stop if escape key is pressed
    k = cv2.waitKey(30) & 0xff
    if k==27:
        break

# Release the VideoCapture object
cap.release()


