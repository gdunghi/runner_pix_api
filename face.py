import face_recognition
from os import path
import os
import json
from object import MyObject
from objectview import Objectview
from pymongo import MongoClient
import numpy as np
from datetime import datetime

class Face:
    def __init__(self, app):
        self.storage = app.config["storage"]
        self.db = app.db
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
        trained_storage = path.join(self.storage, 'trained')
        return path.join(trained_storage, name)
    
    def load_train_all(self):
        return os.listdir(self.storage+ '/trained')

    def load_unknown_file_by_name(self, name):
        unknown_storage = path.join(self.storage, 'unknown')
        return path.join(unknown_storage, name)
    
                        
    def set_default(self,obj):
        if isinstance(obj, set):
            return list(obj)
        raise TypeError
    
    def load_all_train(self):
        for filename in self.load_train_all():
            face_image = face_recognition.load_image_file(self.load_train_file_by_name(filename))
            if (len(face_image) > 0):
                face_image_encoding = face_recognition.face_encodings(face_image)
                if (len(face_image_encoding) > 0):
                    me = MyObject()
                    me.val  = face_image_encoding[0].tolist()
                    self.get_db().faces.insert({"val" : face_image_encoding[0].tolist(),"filename":filename})

                    self.known_encoding_faces.append(face_image_encoding[0])


    def load_all(self):

        results = self.db.select('SELECT faces.id, faces.user_id, faces.filename, faces.created FROM faces')

        for row in results:

            user_id = row[1]
            filename = row[2]

            face = {
                "id": row[0],
                "user_id": user_id,
                "filename": filename,
                "created": row[3]
            }
            self.faces.append(face)

            face_image = face_recognition.load_image_file(self.load_train_file_by_name(filename))
            face_image_encoding = face_recognition.face_encodings(face_image)[0]
            index_key = len(self.known_encoding_faces)
            self.known_encoding_faces.append(face_image_encoding)
            index_key_string = str(index_key)
            self.face_user_keys['{0}'.format(index_key_string)] = user_id

    def recognize(self, unknown_filename):
        unknown_image = face_recognition.load_image_file(self.load_unknown_file_by_name(unknown_filename))
        unknown_encoding_image = face_recognition.face_encodings(unknown_image)[0]

        results = face_recognition.compare_faces(self.known_encoding_faces, unknown_encoding_image)

        print("results", results)

        index_key = 0
        for matched in results:

            if matched:
                # so we found this user with index key and find him
                user_id = self.load_user_by_index_key(index_key)

                return user_id

            index_key = index_key + 1

        return None

    def recognize_from_db(self, unknown_filename):
        print("start load img",datetime.now())
        unknown_image = face_recognition.load_image_file(self.load_unknown_file_by_name(unknown_filename))
        print("end load img",datetime.now())
        print("start  face_encodings img",datetime.now())
        unknown_encoding_image = face_recognition.face_encodings(unknown_image)[0]
        print("end  face_encodings img",datetime.now())
        
        print("start  get  faces ",datetime.now())
        
        for post in self.get_db().faces.find():
            face_val = Objectview(post)
            print("start  compare img",datetime.now())
            
            results = face_recognition.compare_faces([np.asarray(face_val.val)], unknown_encoding_image)
            print("end  compare img",datetime.now())
            
            print("results", results," ",face_val.filename)
            if (results[0] == True): 
               return face_val.filename

        return None
