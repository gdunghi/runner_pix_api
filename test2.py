import face_recognition
from datetime import datetime
from os import path

def load_unknown_file_by_name( name):
    unknown_storage = path.join("storage", 'unknown')
    return path.join(unknown_storage, name)

unknown_image = face_recognition.load_image_file(load_unknown_file_by_name("DSCF2480.jpg"))
face_locations = face_recognition.face_locations(unknown_image, number_of_times_to_upsample=0, model="cnn")
print("start  face_encodings img", datetime.now())
print("  face_locations", face_locations)
unknown_encoding_image = face_recognition.face_encodings(unknown_image,face_locations,100)
print(unknown_encoding_image)