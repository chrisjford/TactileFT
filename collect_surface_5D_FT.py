from FiltDataGather import DataGather
from sample_analysis import Analyser
from cri.robot import SyncRobot, AsyncRobot
from cri.controller import RTDEController
from matplotlib import pyplot as plt
import time, keyboard, pickle, os, shutil
import pandas as pd
import numpy as np

def make_target_df(target_df_file, poses_rng, num_poses, num_frames=1, obj_poses=[[0,]*6], moves_rng=[[0,]*6,]*2, **kwargs):
    np.random.seed(0) # make predictable
    poses = np.random.uniform(low=poses_rng[0], high=poses_rng[1], size=(num_poses, 6))
    poses = poses[np.lexsort((poses[:,1], poses[:,5]))]
    moves = np.random.uniform(low=moves_rng[0], high=moves_rng[1], size=(num_poses, 6))

    pose_ = [f"pose_{_+1}" for _ in range(6)]
    move_ = [f"move_{_+1}" for _ in range(6)]
    target_df = pd.DataFrame(columns=["image_name", "data_name", "obj_id", "pose_id", *pose_, *move_])

    for i in range(num_poses * len(obj_poses)):
        data_name = f"frame_{i}"
        i_pose, i_obj = (int(i%num_poses), int(i/num_poses))
        pose = poses[i_pose,:] + obj_poses[i_obj]
        move = moves[i_pose,:]        
        for f in range(num_frames):
            frame_name = f"frame_{i}_{f}.png"
            target_df.loc[-1] = np.hstack((frame_name, data_name, i_obj+1, i_pose+1, pose, move))
            target_df.index += 1

    target_df.to_csv(target_df_file, index=False)
    return target_df

def collect(target_df, dataPath, resume_from, sleep_time, i):
    flush = False
    for _, row in target_df.iloc[resume_from:].iterrows():
        if not flush:
            # Take first sample and disregard to clear buffer:
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

            i = i+1   
        except:
            print(f'something went wrong sample_{i} - moving on...')
            break

base_frame = (0, 0, 0, 0, 0, 0)  
work_frame = (474, -110, 57, -180, 0, -90)     # base frame: x->front, y->right, z->up
trial = 20

# Resume from last completed sample +1 (0 for new dataset):
resume_from = 0

if resume_from == 0:
    poses_rng = [[0, 0, 1, 20, 20, 0], [0, 0, 4, -20, -20, 0]]
    num_poses = 3000
    num_frames = 1
    moves_rng = [[2, 2, 0, 0, 0, 0], [-2, -2, 0, 0, 0, 0]] # Shear movements

    parent = 'E:/Data'
    folder = f"collect_{trial}_5D_surface"
    dataPath = os.path.join(parent, folder)
    os.mkdir(dataPath)

    target_df = make_target_df(f"{dataPath}/targets.csv", poses_rng, num_poses, num_frames, obj_poses=[[0,]*6], moves_rng=moves_rng)
else:
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
    robot.move_linear((0, 0, 0, 0, 0, 0)) #move to home position
    time.sleep(3)
    dg.start()
    time.sleep(2)
    
    collect(target_df, dataPath, num_frames, sleep_time, i)

    dg.stop()

    robot.linear_speed = 30
    robot.move_linear((0, 0, -50, 0, 0, 0)) #move to home position

