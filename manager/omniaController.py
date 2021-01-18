import json
import os
import logging
import importlib

### Omnia libraries ###
from manager.omniaMediaSharing      import OmniaMediaSharing
### --- ###

class OmniaController:
    """Handle which devices and users are connected, which user can use which devices, etc.
    An OmniaMediaSharing instance is available at 'OMS' attribute.

    Loads apps from devices/apps folder.
    """
    def __init__(self, authorizations_path):
        """Initialization

        :param authorizations_path: path to JSON file containing authorizations. 
                                    Must have this structure:
                                    {
                                        "username1": ["device1", "device2", ... ],  # devices username1 can use
                                        "username2": ["device1", "device2", ... ],  # devices username2 can use
                                        ...
                                    }
        :type authorizations_path: str
        """

        self.devices = []
        self.nearDevices = {}
        self.streamingDevices = []
        self.users = {}

        ### Sharing ###
        self.OMS = OmniaMediaSharing()
        ### --- ###

        ### Logging ###
        logging.getLogger("PIL").setLevel(logging.WARNING)
        self.log = logging.getLogger('OmniaController')
        ### --- ###

        with open(authorizations_path, "r") as rf:
            self.authorizations = json.load(rf)
        
        self.iot_imports = {}

        self.importIOTFunctions()

    def importIOTFunctions(self):
        """Import IoT apps

        :raises ValueError: if devices/apps directory does not exist
        """
        iot_funct_path ="devices/apps"

        if os.path.exists(iot_funct_path):
            iot_functions = next(os.walk(iot_funct_path))[2]
    
            iot_functions.sort()

            for iot in iot_functions:
                appName = iot[:-3]      # remove .py extension
                if appName[0] != "_":   # do not import apps that start with "_"
                    self.log.debug("loading IOT function: {!r}".format(appName.upper()))
                    appObj = getattr(importlib.import_module("devices.apps."+appName), appName.capitalize())
                    self.iot_imports[appName] = appObj
                else:
                    self.log.debug("ignoring IOT function: {!r}".format(appName[1:].upper()))
        else:
            #raise ValueError(f"Cannot find {iot_funct_path} directory.")
            self.log.error(f"Cannot find {iot_funct_path} directory.")
    
    def getIOTFunction(self, username, device_type):
        """Get IoT function for this username and device type

        :param username: username
        :type username: str
        :param device_type: attribute "type" of the device
        :type device_type: str
        :return: IoT app
        :rtype: function object
        """
        if username in self.users:
            if device_type in self.users[username]["iot"]:
                iot_fn = self.users[username]["iot"][device_type]
            else:
                #raise ValueError(f"User '{username}' can't use device of type '{device_type}'")
                self.log.error(f"User '{username}' can't use device of type '{device_type}'")
        else:
            #raise ValueError(f"User '{username}' not found")
            self.log.error(f"User '{username}' not found")
        return iot_fn

    def addDevice(self, device):
        """Adds device to devices list

        :param device: device object
        :type device: Device instance
        """
        self.devices.append(device)
    
    def removeDevice(self, device):
        if device in self.devices:
            self.devices.remove(device)
    
    def addUser(self, user):
        """Adds user in users dict, adding also IoT apps that user is authorized to use

        :param user: dictionary with this structure:
                        {
                            "name": "username"
                            "uid": "user_id"
                        }
        :type user: dict
        """
        username = user["name"]
        user_id = user["uid"]

        iot_functions = {}
        for iot_app_name in self.iot_imports:   # for every iot app imported in importIOTFunctions()
            if iot_app_name in self.authorizations[username]:   # check if user is authorized to use this app
                iot_functions[iot_app_name] = self.iot_imports[iot_app_name](username, self)
        
        self.users[username] =  {
            "uid": user["uid"],
            "iot": iot_functions
        }
    
    def removeUser(self, username):
        if username in self.users:
            self.users.pop(username)

    def __addNearDevice(self, device, username):
        if not (username in self.nearDevices):
            self.nearDevices.__setitem__(username, [])
        
        if not (device in self.nearDevices[username]):
            self.nearDevices[username].append(device)
	
    def __removeNearDevice(self, device, username):
        if username in self.nearDevices:
            if device in self.nearDevices[username]:
                device.stream = False
                self.nearDevices[username].remove(device)
	
    def __updateNearDevices(self, username):
        for device in self.devices:
            if device.isNear:
                if device.getLastNearUser() == self.users[username]["uid"]:
                    if device.name in self.authorizations[username]:
                        self.__addNearDevice(device, username)
            else:
                self.__removeNearDevice(device, user)

    async def listNearDevices(self, username):
        """Returns a list of the devices to which the user is near

        :param username: user id
        :type username: str
        :return: list of devices near
        :rtype: list
        """
        self.__updateNearDevices(username)
        
        availableDevices = []
        #print(self.nearDevices)
        if username in self.nearDevices:
            for device in self.nearDevices[username]:
                #if device.streamingUser == "" or device.streamingUser == username:
                availableDevices.append(device)
        
        #print(availableDevices)
        return availableDevices
    
    '''
    def streamOnDevice(self, dev, user):
        if dev.stream:
            dev.stream = False
            dev.streamingUser = ""
            self.streamingDevices.remove(dev)
            return 0
        else:
            dev.stream = True
            dev.streamingUser = user
            self.streamingDevices.append(dev)

            for device in self.nearDevices:
                if device != dev:
                    if device.streamingUser == user:
                        device.stream=False
                        device.streamingUser = ""
            
            return dev
    '''

    def isValidUser(self, username):
        """Checks if there's this username in users list

        :param username: username to check for
        :type username: str
        :return: True if username is present, False otherwise
        :rtype: bool
        """
        if username in self.users:
            return True
        
        return False
