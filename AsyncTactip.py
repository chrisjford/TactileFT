import cv2, keyboard, time, json, pickle
import numpy as np
from threading import Thread
from vsp.video_stream import CvVideoCamera
from vsp.processor import CameraStreamProcessor, AsyncProcessor

class TacTip(object):
    def __init__(self):
        self.cam = cv2.VideoCapture(1)
        self.cam.set(3, 1280)
        self.cam.set(4, 720)
        self.cam.set(cv2.CAP_PROP_EXPOSURE, -5)
        self.threadRun = False
        
        self._fourcc = cv2.VideoWriter_fourcc(*'MP4V')
        self.frame_width = int(self.cam.get(3))
        self.frame_height = int(self.cam.get(4))
        self.start_time = time.time()
        self.out = cv2.VideoWriter(f'output_{self.start_time}.mp4',self._fourcc, 20, (self.frame_width,self.frame_height))

        self.t = []

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        print('exiting...')
        self.close()
    
    def return_start_time(self):
        return self.start_time

    def start(self):
        self.dataThread = Thread(None, self.displayFrame)
        self.threadRun = True
        self.dataThread.start()
        print('Camera thread started')
    
    def displayFrame(self):
        while self.threadRun:
            self.t.append(time.time())
            # `success` is a boolean and `frame` contains the next video frame
            success, frame = self.cam.read()
            self.out.write(frame)   # write frame to video file
            cv2.imshow("capture", frame)
            cv2.waitKey(1)

            if success == False:
                break

    def stop(self):
        if self.threadRun:
            self.threadRun = False

            self.dataThread.join()
            self.cam.release()
            self.out.release()
            print("Camera thread joined successfully")

            with open(f'video_timestamps_{self.start_time}.pkl', 'wb') as handle:
                pickle.dump(self.t, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def close(self):
        self.stop()