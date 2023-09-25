from FiltDataGather import DataGather
from sample_analysis import Analyser
from cri.robot import SyncRobot, AsyncRobot
from cri.controller import RTDEController
from matplotlib import pyplot as plt
import time, keyboard, pickle, os, shutil
import pandas as pd
import numpy as np

base_frame = (0, 0, 0, 0, 0, 0)  
work_frame = (474, -110, 57, -180, 0, -90)     # base frame: x->front, y->right, z->up
trial = 20

# Resume from last completed sample +1:
resume_from = 14783

Fx = []
Fy = []
Fz = []

dataPath = f'E:/Data/collect_{trial}_5D_surface'
target_df = pd.read_csv(f'{dataPath}/targets.csv')

with DataGather(trial, resume=True, dataPath=dataPath) as dg, AsyncRobot(SyncRobot(RTDEController(ip='192.11.72.20'))) as robot:
    time.sleep(1)
    analyse = Analyser(trial)

    # Setup robot (TCP, linear speed,  angular speed and coordinate frame):
    robot.tcp = (0, 0, 38, 0, 0, -45)
    robot.axes = "sxyz"
    robot.linear_speed = 100
    robot.angular_speed = 100
    robot.coord_frame = work_frame
    sleep_time = 0.5
    angle = 0
    i = resume_from
    flush = False
    # ready_pose = (0, 0, 100.5, 0, 0, 0)
    robot.move_linear((0, 0, 0, 0, 0, 0)) #move to home position
    time.sleep(3)
    # robot.move_linear(ready_pose)
    dg.start()
    time.sleep(2)
    
    for _, row in target_df.iloc[resume_from:].iterrows():
        if not flush:
            # Take first sample as dummy:
            pose = row.loc['pose_1' : 'pose_6'].values.astype(float)
            move = row.loc['move_1' : 'move_6'].values.astype(float)
            print(f'pose for frame_{i} = {pose}')
            tap = [0,0,pose[2],0,0,0]
            pose = (pose - tap)
            robot.move_linear(pose - move)
            dg.begin_sample(i)
            robot.move_linear(pose - move + tap)
            robot.linear_speed = 10
            time.sleep(0.25)
            robot.move_linear(pose + tap)
            time.sleep(sleep_time)
            dg.stop_and_write()
            robot.linear_speed = 200
            robot.move_linear((0, 0, -10, 0, 0, 0))
            time.sleep(sleep_time)
            os.remove(f'{dataPath}/time_series/sample_{i}.pkl')
            shutil.rmtree(f'{dataPath}/videos/sample_{i}')
            flush = True
        else:
            print('flushed - moving on to main samples')
            break

    for _, row in target_df.iloc[resume_from:].iterrows():
        try:
            # Get pose:
            i_obj, i_pose = (int(row.loc["obj_id"]), int(row.loc["pose_id"]))
            pose = row.loc['pose_1' : 'pose_6'].values.astype(float)
            move = row.loc['move_1' : 'move_6'].values.astype(float)
            print(f'pose for frame_{i} = {pose}')
            tap = [0,0,pose[2],0,0,0]
            pose = (pose - tap)
            robot.move_linear(pose - move)
            dg.begin_sample(i)
            robot.move_linear(pose - move + tap)
            robot.linear_speed = 10
            time.sleep(0.25)
            robot.move_linear(pose + tap)
            time.sleep(sleep_time)
            dg.stop_and_write()
            robot.linear_speed = 200
            robot.move_linear((0, 0, -10, 0, 0, 0))
            time.sleep(sleep_time)

            sample_size = os.path.getsize(f'{dataPath}/time_series/sample_{i}.pkl') #check FT sensor is still working

            if sample_size < 55000:
                dg.pause()
                os.remove(f'{dataPath}/time_series/sample_{i}.pkl')
                shutil.rmtree(f'{dataPath}/videos/sample_{i}')
                print(f'sample {i} under threshold at {sample_size}, removed and exiting...')
                break

            # if i%10 == 0 and i != 0:
            #     dg.FTcalibrate()

            i = i+1   
        except:
            print(f'something went wrong sample_{i} - moving on...')
            break

    dg.stop()
    #os.remove(f'C:/Users/c28-ford/Project/FT/data/collect_{trial}_5D_surface/time_series/sample_-1.pkl')
    
    # force_df = pd.DataFrame(list(zip(Fx,Fy,Fz)), columns = ['Fx','Fy','Fz'])
    # force_df.to_csv(f"collect_5D_edge_{trial}_forces.csv")
    # print(df.head())
    

    robot.linear_speed = 30
    robot.move_linear((0, 0, -50, 0, 0, 0)) #move to home position

