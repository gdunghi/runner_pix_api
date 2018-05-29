import face_recognition
from os import path
import os
import json
from object import MyObject
from objectview import Objectview
from pymongo import MongoClient
import numpy as np
from datetime import datetime
import threading
from active_pool import ActivePool
import logging
from multiprocessing import Pool
import base64

class Face:
    def __init__(self, app):
        self.storage = app.config["storage"]
        # self.db = app.db
        self.faces = []  # storage all faces in caches array of face object
        self.known_encoding_faces = []  # faces data for recognition
        self.face_user_keys = {}
        # self.load_all()

    def get_db(self):
        client = MongoClient('188.166.212.73:27017')
        db = client.myFirstMB
        return db

    def load_user_by_index_key(self, index_key=0):

        key_str = str(index_key)

        if key_str in self.face_user_keys:
            return self.face_user_keys[key_str]

        return None

    def load_train_file_by_name(self, name):
        trained_storage = path.join(self.storage, "trained")
        return path.join(trained_storage, name)

    def load_train_all(self):
        return os.listdir(self.storage + '/trained')

    def load_unknown_file_by_name(self, name):
        unknown_storage = path.join(self.storage, 'unknown')
        return path.join(unknown_storage, name)

    def set_default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        raise TypeError
    
    def execute_train(self,filename, s, pool):
      
        print('Waiting to join the pool')
        with s:
            name = threading.current_thread().getName()
            pool.makeActive(name)
            face_image = face_recognition.load_image_file(self.load_train_file_by_name(filename))
            if (len(face_image) > 0):
                face_image_encoding = face_recognition.face_encodings(
                    face_image)
                if (len(face_image_encoding) > 0):
                    me = MyObject()
                    me.val = face_image_encoding[0].tolist()
                    self.get_db().faces.insert({"val": face_image_encoding[0].tolist(), "filename": filename})
            pool.makeInactive(name)
    
    def execute_process_training(self,filename):
        print("Processing... ",filename)
        face_image = face_recognition.load_image_file(self.load_train_file_by_name(filename))

        face_locations = face_recognition.face_locations(face_image, number_of_times_to_upsample=0, model="cnn")
        
        if (len(face_image) > 0):
            print("start face_encodings ..",filename," ", datetime.now())
            face_image_encoding = face_recognition.face_encodings(face_image,face_locations,100)
            print("end face_encodings ..",filename," ", datetime.now())
            
            if (len(face_image_encoding) > 0):
                me = MyObject()
                me.val = face_image_encoding[0].tolist()
                print("start saving ..",filename," ", datetime.now())
                self.get_db().faces.insert({"val": face_image_encoding[0].tolist(), "filename": filename})
                print("start save ..",filename," ", datetime.now())
            
    def load_all_train(self):
        # threads = []
        # pool = ActivePool()
        # s = threading.Semaphore(6)
        # for filename in self.load_train_all():
        #     t = threading.Thread(name='execute_train_'+filename, target=self.execute_train, args=(filename, s, pool,))
        #     threads.append(t)
        #     t.start()
        
        # job = []
        # pool = ActivePool()
        # s = threading.Semaphore(6)

        # p = Pool(4)
        # p.map(self.execute_process_training, self.load_train_all())
        for filename in self.load_train_all():
            if filename.endswith(".jpg"):
                self.execute_process_training(filename)
           
    
    def train_image(self, image_path, filename):
       
        face_image = face_recognition.load_image_file(image_path+"/"+filename)
        if (len(face_image) > 0):
            face_image_encoding = face_recognition.face_encodings(face_image)
            if (len(face_image_encoding) > 0):
                me = MyObject()
                me.val = face_image_encoding[0].tolist()
                return self.get_db().faces.insert({"val": face_image_encoding[0].tolist(), "filename": filename})

    def recognize_from_db(self, unknown_filename):
        unknown_image = face_recognition.load_image_file(self.load_unknown_file_by_name(unknown_filename))
        face_locations = face_recognition.face_locations(unknown_image, number_of_times_to_upsample=0, model="cnn")
        print("start  face_encodings img", datetime.now())
        unknown_encoding_image = face_recognition.face_encodings(unknown_image,face_locations,100)
        print("end  face_encodings img", datetime.now())

        if len(unknown_encoding_image) > 0:
            print("start  get  faces ", datetime.now())
            matched_images = []
            for face in unknown_encoding_image:
                for post in self.get_db().faces.find():
                    face_val = Objectview(post)
                    print("start  compare img", datetime.now())
                    print("compare with img", face_val.filename)
                    

                    results = face_recognition.compare_faces([np.asarray(face_val.val)], face)
                    print("end  compare img", datetime.now())

                    print("results", results, " ", face_val.filename)
                    if (results[0] == True):
                        matched_images.append(face_val.filename)
                    
            if(len(matched_images)>0):
                # return self.convert_base64_image(matched_images)
                return matched_images
                
        return None

    def convert_base64_image(self,images):
        base64_images = []
        trained_path = path.join(self.storage, 'trained')
        for image in images:
            with open(path.join(trained_path,image), "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read())
                base64_images.append(encoded_string.decode('utf-8'))


        return base64_images