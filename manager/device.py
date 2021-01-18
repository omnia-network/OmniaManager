import curio
import logging

### Omnia libraries ###
from core.omniaProtocol             import OmniaProtocol
from modules.omniaConnectivity      import OmniaBLE

from devices.apps.display import Display
from devices.apps.screen  import Screen
'''# used for tests
#from devices.apps.sound import Sound
#from devices.apps.screen import Screen
#from devices.apps.display import Display'''
### --- ###

class Device:

    DEFAULT_WAIT_TIME = 0.1
    WAIT_TIME_IOT = 0.001
    MIN_BLE_RSSI = -70

    def __init__(self, socket, address, device_data, omniaController=None):

        ### Socket ###
        self.socket = socket
        self.address = address    # (IPAddress, Port)
        ### --- ###

        ### Device data ###
        '''
        device_data structure
        {
            "name": "device_name",
            "class": "device_type"
        }
        '''        
        self.device_data = device_data
        self.device_data["type"] = "device"
        self.name = device_data["name"]     # device name
        self.type = device_data["class"]   # device type
        ### --- ###

         ### Omnia Protocol ###
        self.omniaProtocol = OmniaProtocol(self.socket, self.device_data)
        ### --- ###

        ### Omnia Controller ###
        self.omniaController = omniaController
        ### --- ###

        ### Omnia libraries ###
        self.omniaBLE = OmniaBLE(self.omniaProtocol, self.omniaController)
        ### --- ###

        ### Proximity detection ###
        self.is_near = False    # True when a user is detected
        self.connect_later = []     # list users that can connect later
        self.last_near_user = None
        ### --- ###

        ### Streaming ###
        self.stream = False     # True if the device is being used
        self.streaming_user = ""    # id of the user that is using this device
        ### --- ###

        ### IOT functions ###
        self.iot_function = None    # class from src/iot_funct that performs a function
        ### --- ###

        ### Logging ###
        logging.getLogger("PIL").setLevel(logging.WARNING)  # disable PIL library logging
        self.log = logging.getLogger(
            "[{}_{}_{}]: main".format(self.name, *self.address)
        )
        ### --- ###

    # get initial configuration of pins and settings
    async def initConfig(self):
        pass
        #await self.omniaProtocol.calculateLatency(iterations=30, callback=self.latencyCallback)

    def latencyCallback(self, latency):
        self.log.debug(latency)

    async def runIOTFunction(self, iot_function):
        """Sets the function the device have to run

        :param iot_function: function to be run
        :type iot_function: function object
        """
        self.log.debug("Running iot function {!r}".format(iot_function))
        #self.omniaClass.stopRecvNFC()
        await self.omniaBLE.stopBLEScan()   # stop scanning for BLE proximity
        await iot_function.start()    # execute the start function from iot_function class
        self.iot_function = iot_function    # set the new iot_function to run
    
    async def __runIOT(self):
        """Keep running selected iot_function
        """
        while True:
            if self.iot_function:
                await self.iot_function.run()     # run iot_function and return

                wait_time = self.WAIT_TIME_IOT  # wait time for iot function (default)
                
                # check if iot_function has a timing that needs to be respected
                if hasattr(self.iot_function, "time_sleep"):
                    if self.iot_function.time_sleep > 0:
                        wait_time = self.iot_function.time_sleep
                
                await curio.sleep(wait_time)
            else:
                await curio.sleep(self.DEFAULT_WAIT_TIME)
    
    def scanCallback(self, user_id):
        """Callback from OmniaConnectivity library

        :param user_id: username scanned
        :type user_id: str
        """
        self.last_near_user = user_id

    def getLastNearUser(self):
        return self.last_near_user

    def streamLater(self, username):
        """Enable username to stream later

        :param username: username to add
        :type username: str
        """
        if not username in self.connect_later:
            self.connect_later.append(username)
    
    def canStreamLater(self, username):
        """Return if user can stream later on this device

        :param username: username to check
        :type username: str
        :return: True if the user can stream later
        :rtype: bool
        """
        if username in self.connect_later:
            return True

        return False
    
    async def resetStreamingUser(self):
        """Stop running iot_function and reset streaming parameters
        """
        self.log.debug("Resetting streaming user")

        self.streamLater(self.streaming_user)   # remember user to stream later

        self.streaming_user = ""
        self.stream = False

        self.omniaBLE.scanBLE(self.scanCallback)    # listen to BLE again
        self.iot_function = None    # reset iot_function
    
    def setStreamingUser(self, user):
        """Sets who is using the device, sets stream flag to True

        :param user: user that is using this device
        :type user: str
        """
        self.streaming_user = user
        self.stream = True

    def getStreamingUser(self):
        return self.streaming_user

    def getDeviceName(self):
        return self.name

    def getDeviceType(self):
        return self.type

    async def main(self):
        
        # initialize configuration of pins and settings
        _ = await self.omniaProtocol.addTask(self.initConfig, wait_for_execution=True)

        '''# used for tests

        # s = Sound("eulero", None)
        # await s.handleStreaming(self)
        # await self.runIOTFunction(s)

        # f = Screen("eulero", None)
        # await f.handleStreaming(self)
        # await self.runIOTFunction(f)

        # f = Display("eulero", None)
        # await f.handleStreaming(self)
        # await self.runIOTFunction(f)

        # self.omniaController.addUser({"name": "eulero", "uid":"eulero"})
        # self.omniaController.omnia_media_sharing.setAttribute("eulero", "pause", True)

        # f = self.omniaController.getIOTFunction("eulero", self.type)
        # await f.handleStreaming(self)
        # await self.runIOTFunction(f)'''

        # self.omniaClass.startRecvNFC(self.NFCCallback)
        await self.omniaBLE.scanBLE(self.scanCallback)

        self.omniaController.OMS.setAttribute("eulero", "song_id", 0)
        self.omniaController.OMS.setAttribute("eulero", "duration", 360)
        self.omniaController.OMS.setAttribute("eulero", "elapsed_time", 0)

        #f = Display("eulero", self.omniaController)
        f = Screen("eulero", self.omniaController)
        await f.handleStreaming(self)
        await self.runIOTFunction(f)

        ## run omniaProtocol with loop
        await self.omniaProtocol.begin(self.__runIOT)

        

    async def resumeSocket(self, new_socket):
        await self.omniaProtocol.resumeSocket(new_socket)

        # initialize configuration of pins and settings
        _ = await self.omniaProtocol.addTask(self.initConfig, wait_for_execution=True)

        self.log.debug("resumed")
        
    async def resumeEventListener(self, event):

        await event.wait()

        return self
