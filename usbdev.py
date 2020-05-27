from pyudev import Context, Monitor, MonitorObserver
import os

class usbScan():

    def __init__(self):
        # some globals for the device details
        self.USBDEV_UUID = None
        self.USBDEV_VENDOR = None
        self.USBDEV_SERID = None
        self.USBDEV_FSTYPE = None
        self.USBDEV_MODEL = None
        self.USBDEV_DEVPATH = None
        self.USBDEV_HAVEDATA = False
                
    # callback when a usb device is plugged in
    def usbEventCallback(self, action, device):
        if action == 'add':
            # store the device values
            self.USBDEV_VENDOR = device.get('ID_VENDOR')
            self.USBDEV_SERID = device.get('ID_SERIAL')
            self.USBDEV_UUID = device.get('ID_FS_UUID')
            self.USBDEV_FSTYPE = device.get('ID_FS_TYPE')
            self.USBDEV_MODEL = device.get('ID_MODEL')
            self.USBDEV_DEVPATH = device.get('DEVNAME')
    
            self.USBDEV_HAVEDATA = True
        elif action == 'remove':
            # clear the device data
            self.USBDEV_VENDOR = None
            self.USBDEV_SERID = None
            self.USBDEV_UUID = None
            self.USBDEV_FSTYPE = None
            self.USBDEV_MODEL = None
            self.USBDEV_DEVPATH = None
            self.USBDEV_HAVEDATA = False


    def startListener(self):
        # create a context, create monitor at kernel level, select devices
        context = Context()
        monitor = Monitor.from_netlink(context)
        monitor.filter_by(subsystem='block')
    
        observer = MonitorObserver(monitor, usbEventCallback, name="usbdev")
        # set this as the main thread
        observer.setDaemon(False)
        observer.start()
    
        return observer
    
    
    def isDeviceConnected(self):
        self.USBDEV_HAVEDATA
        return self.USBDEV_HAVEDATA
    
    
    def getDevData(self):
        if self.isDeviceConnected():
            return {'UUID': self.USBDEV_UUID,
                    'SERID': self.USBDEV_SERID,
                    'VENDOR': self.USBDEV_VENDOR,
                    'FSTYPE': self.USBDEV_FSTYPE,
                    'MODEL': self.USBDEV_MODEL,
                    'DEVPATH': self.USBDEV_DEVPATH}
        return None
    
    
    def stopListener(observer):
        observer.stop()
    
    
    # returns the accesible path of the device on the Raspberry pi
    # you can change how the path gets calulated.
    def getMountPathUsbDevice(self):
        sudoPassword = 'mycroft'
        if not isDeviceConnected() or self.USBDEV_DEVPATH == None:
            return None
        # check if the dev path exists
        if os.path.exists(self.USBDEV_DEVPATH):
            # create a mount directory
            if not os.path.exists('mp'):
                os.makedirs('mp')
            command = "mount " + self.USBDEV_DEVPATH + " mp"
            p = os.system('echo %s|sudo -S %s' % (sudoPassword, command))
            # mount the dev path to the folder
            # os.system("mount " + self.USBDEV_DEVPATH + " mp")
            # return the path to the folder from root
            truePath = os.getcwd() + '/mp'
            return truePath
        return None