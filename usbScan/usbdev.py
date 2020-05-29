# usb monitoring event
from pyudev import Context, Monitor, MonitorObserver
import os

# some globals for the device details
USBDEV_UUID = None
USBDEV_VENDOR = None
USBDEV_SERID = None
USBDEV_FSTYPE = None
USBDEV_MODEL = None
USBDEV_DEVPATH = None

USBDEV_HAVEDATA = False


# callback when a usb device is plugged in
def usbEventCallback(action, device):
    global USBDEV_UUID
    global USBDEV_VENDOR
    global USBDEV_SERID
    global USBDEV_FSTYPE
    global USBDEV_MODEL
    global USBDEV_DEVPATH

    global USBDEV_HAVEDATA

    if action == 'add':
        # store the device values
        USBDEV_VENDOR = device.get('ID_VENDOR')
        USBDEV_SERID = device.get('ID_SERIAL')
        USBDEV_UUID = device.get('ID_FS_UUID')
        USBDEV_FSTYPE = device.get('ID_FS_TYPE')
        USBDEV_MODEL = device.get('ID_MODEL')
        USBDEV_DEVPATH = device.get('DEVNAME')

        USBDEV_HAVEDATA = True

    elif action == 'remove':
        # clear the device data
        USBDEV_VENDOR = None
        USBDEV_SERID = None
        USBDEV_UUID = None
        USBDEV_FSTYPE = None
        USBDEV_MODEL = None
        USBDEV_DEVPATH = None
        USBDEV_HAVEDATA = False


def startListener():
    # create a context, create monitor at kernel level, select devices
    context = Context()
    monitor = Monitor.from_netlink(context)
    monitor.filter_by(subsystem='block')

    observer = MonitorObserver(monitor, usbEventCallback, name="usbdev")
    # set this as the main thread
    observer.setDaemon(False)
    observer.start()

    return observer


def isDeviceConnected():
    global USBDEV_HAVEDATA
    return USBDEV_HAVEDATA


def getDevData():
    if isDeviceConnected():
        global USBDEV_UUID
        global USBDEV_VENDOR
        global USBDEV_SERID
        global USBDEV_FSTYPE
        global USBDEV_MODEL
        global USBDEV_DEVPATH
        return {'UUID': USBDEV_UUID,
                'SERID': USBDEV_SERID,
                'VENDOR': USBDEV_VENDOR,
                'FSTYPE': USBDEV_FSTYPE,
                'MODEL': USBDEV_MODEL,
                'DEVPATH': USBDEV_DEVPATH}
    return None


def stopListener(observer):
    observer.stop()


# returns the accesible path of the device on the Raspberry pi
# you can change how the path gets calulated.
def getMountPathUsbDevice(password):
    sudoPassword = password #'mycroft'
    global USBDEV_DEVPATH
    if not isDeviceConnected() or USBDEV_DEVPATH == None:
        return None

    # check if the dev path exists
    if os.path.exists(USBDEV_DEVPATH):

        # create a mount directory
        if not os.path.exists('mp'):
            os.makedirs('mp')
        #"mount", "-t", "auto"
        command = "mount -t auto" + USBDEV_DEVPATH + " mp"
        p = os.system('echo %s|sudo -S %s' % (sudoPassword, command))

        # mount the dev path to the folder
        # os.system("mount " + USBDEV_DEVPATH + " mp")

        # return the path to the folder from root
        truePath = os.getcwd() + '/mp'

        return truePath

    return None

def uMountPathUsbDevice(password):
    sudoPassword = password #'mycroft'
    global USBDEV_DEVPATH
    if USBDEV_DEVPATH == None:
        return None

    # check if the dev path exists
    if os.path.exists(USBDEV_DEVPATH):
        command = "umount " + USBDEV_DEVPATH + " mp"
        p = os.system('echo %s|sudo -S %s' % (sudoPassword, command))
        # unmount the dev path to the folder

    return None