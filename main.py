import cv2
import numpy as np
import datetime
import redis
import pymongo

myclient = pymongo.MongoClient('mongodb://localhost:27017/')
mydb = myclient['mydb']
mycol = mydb["times"]

r = redis.Redis(host='localhost', port=6379, db=0)

startX = 0
startY = 0
endX = 0
endY = 0
threshold = 0
count = 0
readstatus = 0
diffsum = []
writeimg = False

cam = cv2.VideoCapture('vdotesting.mp4')

for i in range(10):
    ret, frame = cam.read()
    cv2.imwrite('background/'+str(i+1)+'.jpg', frame)

while True:
    state = int(r.get('state'))
    if state == 0:
        writeimg = False
        continue
    elif state == 1:
        if not writeimg:
            img = cv2.imread('background/5.jpg')
            writeimg = cv2.imwrite(
                'backend node/public/image/background.jpg', img)

    elif state == 2:
        startX = int(r.get('x'))
        startY = int(r.get('y'))
        endX = int(r.get('w'))
        endY = int(r.get('h'))
        threshold = ((endX-startX) * (endY-startY))*0.2
        crop = np.zeros((endY-startY, endX-startX), dtype=float)
        for i in range(10):
            img = cv2.imread('background/'+str(i+1)+'.jpg', 0)
            cropImg = img[startY:endY, startX:endX]
            crop = crop + cropImg
        mcrop = crop/10
    elif state == 3:
        ret, frame = cam.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        graycrop = gray[startY:endY, startX:endX]
        difference = cv2.absdiff(graycrop, np.ubyte(mcrop))
        _, difference = cv2.threshold(difference, 50, 1, cv2.THRESH_BINARY)
        diffsum.append(np.sum(difference))

        if len(diffsum) == 10:
            del diffsum[0]

        if np.average(diffsum) >= threshold:
            if readstatus == 0:
                readstatus = 1
                # mycol.insert_one({'time': datetime.datetime.utcnow()})
                print(datetime.datetime.now())
            img = cv2.rectangle(frame, (startX, startY),
                                (endX, endY), (255, 0, 0), 2)
        else:
            readstatus = 0
            img = cv2.rectangle(frame, (startX, startY),
                                (endX, endY), (0, 0, 255), 2)

        count = count + 1
        cv2.imwrite('backend node/public/image/img'+str(count)+'.jpg', img)
        r.set('count', count)
        if(count >= 100):
            count = 0

        cv2.imshow('vdo', frame)

        if cv2.waitKey(1) & 0xFF == ord('a'):
            break

        if not ret:
            break

        if 0xff == ord('a'):
            break

r.set('state', 0)
cam.release()
cv2.destroyAllWindows()
