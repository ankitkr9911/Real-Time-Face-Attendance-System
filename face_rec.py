import numpy as np
import pandas as pd
import cv2

import redis

from insightface.app import FaceAnalysis
from sklearn.metrics import pairwise

import time
from datetime import datetime
import os

hostname = 'redis-18916.c83.us-east-1-2.ec2.redns.redis-cloud.com'
port = 18916
password = 'vTig9W0x2XtLCyR3MDFQFyZjSMSId6Gr'
r = redis.StrictRedis(host=hostname,
                      port=port,
                      password=password)
# extracting data from redis database
def retrive_data(name):
    retrive_dict = r.hgetall(name)
    retrive_series = pd.Series(retrive_dict)
    retrive_series = retrive_series.apply(lambda x:np.frombuffer(x,dtype=np.float32))
    index = retrive_series.index
    index = list(map(lambda x: x.decode(),index))
    retrive_series.index = index
    retrive_df = retrive_series.to_frame().reset_index()
    retrive_df.columns = ['name_role','Facial Feature']
    retrive_df[['Name','Role']] = retrive_df['name_role'].apply(lambda x : x.split('@')).apply(pd.Series)
    return retrive_df[['Name','Role','Facial Feature']]

# Configure face analysis
face_app = FaceAnalysis(name='buffalo_l',
                        root='insightface_model',
                        providers=['CPUExecutionProvider'])
face_app.prepare(ctx_id=0,det_size=(640,640),det_thresh=0.5)

# def ml_search_algorithm(dataframe,feature_column,test_vector,name_role=['Name','Role'],thresh=0.5):
    
#     # cosine similarity based search algorithm
#     # feature_column --> column name that contains features(embeddings) in dataframe

#     dataframe = dataframe.copy()

#     X_list = dataframe[feature_column].tolist()
#     x = np.asarray(X_list)

#     # Debugging step: print shape of each embedding
#     for idx, item in enumerate(X_list):
#         print(f"Item {idx} shape: {np.array(item).shape}")
 
#     try:
#         x = np.asarray(X_list)
#     except ValueError as e:
#         print("Error converting X_list to array:", e)
#         # Handle inconsistent shapes here, for example, by filtering out invalid items
#         return 'Unknown', 'Unknown'
 

#     similar = pairwise.cosine_similarity(x,test_vector.reshape(1,-1))
#     similar_arr = np.array(similar).flatten()
#     dataframe['cosine'] = similar_arr

#     data_filter = dataframe.query(f'cosine >= {thresh}')
#     if(len(data_filter) > 0):
#         data_filter.reset_index(drop=True,inplace=True)
#         argmax = data_filter['cosine'].argmax()
#         person_name,person_role = data_filter.loc[argmax][name_role]
#     else:
#         person_name = 'Unknown'
#         person_role = 'Unknown'
        
#     return person_name,person_role

def ml_search_algorithm(dataframe, feature_column, test_vector, name_role=['Name', 'Role'], thresh=0.5):
    # cosine similarity based search algorithm
    dataframe = dataframe.copy()
    X_list = dataframe[feature_column].tolist()
    
    # Check if all embeddings have the same shape as the test vector
    valid_indices = []
    valid_embeddings = []
    
    # Get test vector shape (usually 512 for InsightFace)
    test_dim = test_vector.shape[0]
    
    # Filter out embeddings with inconsistent shapes
    for idx, item in enumerate(X_list):
        try:
            item_array = np.array(item)
            if item_array.shape[0] == test_dim:
                valid_indices.append(idx)
                valid_embeddings.append(item_array)
        except:
            print(f"Skipping item {idx} due to shape issue")
    
    if len(valid_embeddings) == 0:
        print("No valid embeddings found in database")
        return 'Unknown', 'Unknown'
    
    # Create a new array with only valid embeddings
    x = np.vstack(valid_embeddings)
    
    # Create a new filtered dataframe
    filtered_df = dataframe.iloc[valid_indices].copy()
    
    # Calculate similarity
    similar = pairwise.cosine_similarity(x, test_vector.reshape(1, -1))
    similar_arr = np.array(similar).flatten()
    
    # Add similarity scores to filtered dataframe
    filtered_df['cosine'] = similar_arr
    
    # Filter by threshold
    data_filter = filtered_df.query(f'cosine >= {thresh}')
    
    if len(data_filter) > 0:
        data_filter.reset_index(drop=True, inplace=True)
        argmax = data_filter['cosine'].argmax()
        person_name, person_role = data_filter.loc[argmax][name_role]
    else:
        person_name = 'Unknown'
        person_role = 'Unknown'
        
    return person_name, person_role
class RealTimePred:
    def __init__(self):
        self.logs = dict(name=[],role=[],current_time=[])

    def reset_dict(self):
        self.logs = dict(name=[],role=[],current_time=[])

    def saveLogs_redis(self):
        dataframe = pd.DataFrame(self.logs)

        dataframe.drop_duplicates('name',inplace=True)

        name_list = dataframe['name'].tolist()
        role_list = dataframe['role'].tolist()
        ctime_list = dataframe['current_time'].tolist()
        encoded_data = []

        for name,role,ctime in zip(name_list,role_list,ctime_list):
            if name != 'Unknown':
                concat_string = f'{name}@{role}@{ctime}'
                encoded_data.append(concat_string)

        if len(encoded_data) > 0:
            r.lpush('attendance:logs',*encoded_data)   

        self.reset_dict()    


    def face_prediction(self,test_image,dataframe,feature_column,name_role=['Name','Role'],thresh=0.5):
        current_time = str(datetime.now().strftime('%Y-%m-%d %H:%M'))
        results = face_app.get(test_image)
        test_copy = test_image.copy()
        for res in results:
            x1,y1,x2,y2 = res['bbox'].astype(int)
            embeddings = res['embedding']

            person_name,person_role = ml_search_algorithm(dataframe,'Facial Feature',
                                                            test_vector=embeddings,
                                                            name_role=name_role,
                                                            thresh=thresh)

            if person_name=='Unknown':
                color = (0,0,255)
            else:
                color = (0,255,0)
            cv2.rectangle(test_copy,(x1,y1),(x2,y2),color,2)
            text_gen = person_name
            cv2.putText(test_copy,text_gen,(x1,y1),cv2.FONT_HERSHEY_DUPLEX,0.7,color,2)
            cv2.putText(test_copy,current_time,(x1,y2+20),cv2.FONT_HERSHEY_DUPLEX,0.7,color,2)

            # save info in logs dict
            self.logs['name'].append(person_name)
            self.logs['role'].append(person_role)
            self.logs['current_time'].append(current_time)

        return test_copy



# Registration Form
class RegistrationForm:
    def __init__(self):
        self.sample = 0 

    def reset(self):
        self.sample = 0

    def get_embedding(self,frame):
        # get results from insightface model
        results = face_app.get(frame,max_num=1)
        embeddings = None
        for res in results:
            self.sample = self.sample + 1
            x1,y1,x2,y2 = res['bbox'].astype(int)
            cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,0),2)
            
            # put text samples info
            text = f"samples : {self.sample}"
            cv2.putText(frame,text,(x1,y1),cv2.FONT_HERSHEY_DUPLEX,0.6,(0,255,0),2)
            
            embeddings = res['embedding']

        return frame,embeddings
    

    def save_data_in_redis_db(self,name,role):
        if name is not None:
            if name.strip() != '':
                key = f'{name}@{role}'
            else:
                return 'name_false'
        else:
            return  'name_false'
        
        if 'face_embedding.txt' not in os.listdir():
            return 'file_false'
        # step 1 : load "face_embedding.txt"
        x_array = np.loadtxt('face_embedding.txt',dtype=np.float32) # flatten array

        # step 2 : convert into array (proper shape)
        received_samples = int(x_array.size/512)
        x_array = x_array.reshape(received_samples,512)

        # step 3 : cal. mean embeddings
        x_mean = x_array.mean(axis=0)
        x_mean_bytes = x_mean.tobytes()

        # step 4 : save this into redis database (redis hashes)
        r.hset(name='academy:register',key=key,value=x_mean_bytes)

        os.remove('face_embedding.txt')
        self.reset()
        return True
