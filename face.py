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
    # Draw the rectangle around each face
    for (x, y, w, h) in faces:
        cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
    # Display
    cv2.imshow('img', img)
    
    if len(faces) > 0:
        # check to make sure it's been at least two seconds since the last time we checked for faces
        if current_seconds - start_secs_face >= 2:
            face_count += len(faces)
            print("We found some faces: " + str(len(faces)) + " to be exact! (Pending sync: " + str(face_count) + ")")
            start_secs_face = int(round(time.time()))
    
    # create an outbound note every 5 minutes with accumulated face counts
    if current_seconds - start_secs_note >= 300:
        send_note(face_count)
        print("Sending a new note with " + str(face_count) + " faces.")
        face_count = 0
        start_secs_note = int(round(time.time()))
    
    # Stop if escape key is pressed
    k = cv2.waitKey(30) & 0xff
    if k==27:
        break

# Release the VideoCapture object
cap.release()


