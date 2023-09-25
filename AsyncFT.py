import NetFT
import time
from threading import Thread, Lock

class ATIMINI(object):
    def __init__(self):
        self.ip = '192.168.1.1'
        self.FT18690 = NetFT.Sensor(self.ip)
        print('connected to ATI Mini! \n Calibrating...')
        self.FT18690.tare(1000)#Subtracts the mean average of 1000 samples from new data to
        print('calibration complete')

        self.FxNewtons = None
        self.FyNewtons = None
        self.FzNewtons = None

        self.threadRun = False

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        print('exiting...')
        self.close()

    def start(self):
        self.dataThread = Thread(None, self.readFData)
        self.threadRun = True
        self.dataThread.start()
        print('FT thread started')

    def readFData(self):
        while self.threadRun:
            dataCounts = self.FT18690.getMeasurement()#Get a single sample of all data Fx, Fy, Fz, Tx, Ty, Tz returned as list[6]
            
            self.FxNewtons = dataCounts[0]/1000000
            self.FyNewtons = -1*(dataCounts[1]/1000000)
            self.FzNewtons = -1*(dataCounts[2]/1000000)
            
    
    def getFData(self):
        lock.acquire()
        data = [self.FxNewtons, self.FyNewtons, self.FzNewtons]
        lock.release()
        return data

    def stop(self):
        if self.threadRun:
            self.threadRun = False

            self.dataThread.join()
            print("FT thread joined successfully")

    def close(self):
        self.stop()

lock = Lock()