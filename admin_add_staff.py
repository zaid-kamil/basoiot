from firebase import firebase
import subprocess as pro
import hashlib
import time
from pyfingerprint.pyfingerprint import PyFingerprint

PYVERSION = 'python'
LIB_PATH = "/usr/share/doc/python-fingerprint/examples/example_enroll.py"
FIREBASE ='https://basoiot-a66d0.firebaseio.com/'
STAFF ="/Staff"
USER = '/Users'
ATTD = '/Attendance'

def add_fingerprint(fb,uid,fingerprint="no fingerprint"):
    fb.put(STAFF+'/'+uid,name='fingerprint',data=fingerprint)
    print("saved")

def find_person_id(fb,email):
    staff=fb.get(STAFF,None)
    for key in staff:
        member = staff.get(key)
        for attr in member:
            if email in member.get(attr):
                return key
    return None


def enroll_index_finger():
    ## Enrolls new finger
    ##

    ## Tries to initialize the sensor
    try:
        f = PyFingerprint('/dev/ttyUSB0', 57600, 0xFFFFFFFF, 0x00000000)

        if (f.verifyPassword() == False):
            raise ValueError('The given fingerprint sensor password is wrong!')

    except Exception as e:
        print('The fingerprint sensor could not be initialized!')
        print('Exception message: ' + str(e))
        return None

    ## Gets some sensor information
    print('Currently used templates: ' + str(f.getTemplateCount()) + '/' + str(f.getStorageCapacity()))

    ## Tries to enroll new finger
    try:
        print('waiting for user')
        while (f.readImage() == False):
            pass

        ## Converts read image to characteristics and stores it in charbuffer 1
        f.convertImage(0x01)

        ## Checks if finger is already enrolled
        result = f.searchTemplate()
        positionNumber = result[0]

        if (positionNumber >= 0):
            print('Template already exists at position #' + str(positionNumber))
            return None
        time.sleep(2)
        ## Wait that finger is read again
        while (f.readImage() == False):
            pass
        ## Converts read image to characteristics and stores it in charbuffer 2
        f.convertImage(0x02)
        ## Compares the charbuffers
        if (f.compareCharacteristics() == 0):
            raise Exception('Fingers do not match')

        ## Creates a template
        f.createTemplate()

        ## Saves template at new position number
        positionNumber = f.storeTemplate()
        # print('New template position #' + str(positionNumber))
        f.loadTemplate(positionNumber, 0x01)
        characterics = str(f.downloadCharacteristics(0x01)).encode('utf-8')
        shaprint = hashlib.sha256(characterics).hexdigest()
        return shaprint

    except Exception as e:
        print('Operation failed!')
        print('Exception message: ' + str(e))
        return None

def main():
    email= input("enter staff email")
    if email:
        fb = firebase.FirebaseApplication(FIREBASE, None)
        uid=find_person_id(fb,email)
        fingerprint=enroll_index_finger()
        if uid and fingerprint:
            print('saving online')
            add_fingerprint(fb,uid,fingerprint)
