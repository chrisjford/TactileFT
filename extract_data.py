from sample_analysis import Analyser
import pandas as pd
from tqdm import tqdm
import os, shutil

missing_samples = []
missing_frames = []
Fx = []
Fy = [] 
Fz = []
frames = []
dataPath = f'E:/Data/ftp_24'
videopath = f'E:/Data/ftp_24/videos'
framePath = f'{dataPath}/raw_frames'
analyse = Analyser(f'{dataPath}/time_series')
sample_range = (0,3000)

print('extracting data...')

for i in tqdm(range(sample_range[0], sample_range[1])):
    try:
        # Get forces:
        forces = analyse.get_data_and_labels(i)
        Fx.append(forces[0])
        Fy.append(forces[1])
        Fz.append(forces[2])
        frames.append(f'frame_{i}')
        
        # Get frame:
        filename = os.listdir(f'{videopath}/sample_{i}')
        shutil.copy(f'{videopath}/sample_{i}/{filename[0]}', f'{framePath}/frame_{i-12000}.png')
    except:
        missing_samples.append(i)
        Fx.append(0)
        Fy.append(0)
        Fz.append(0)
        frames.append(f'frame_{i}')
        #i = i+1
        pass

force_df = pd.DataFrame(list(zip(frames,Fx,Fy,Fz)), columns = ['data_name_force','Fx','Fy','Fz'])

df = pd.read_csv(f'{dataPath}/targets.csv')

final_df = pd.concat([df, force_df], axis=1)

for sample_name in missing_samples:
    ind = final_df[(final_df['pose_id'] == (sample_name+1))].index
    final_df.drop(ind)

final_df.to_csv(f"{dataPath}/labels.csv")
print('done')
print(f'missing samples: {missing_samples}')
print(f'missing frames: {missing_frames}')