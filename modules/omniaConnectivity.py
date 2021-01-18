import logging

### Omnia libraries ###
from core.omniaMessageTypes      import OmniaMessageTypes as OMT
### --- ###

"""Utilities for short range connectivity and user interaction
"""

class OmniaBLE:
    """Utilities for BLE interaction
    """

    def __init__(self, omniaProtocol, omniaController, min_rssi=-70):
        """Initialization

        :param omniaProtocol: low-level OmniaProtocol
        :type omniaProtocol: OmniaProtocol instance
        :param omniaProtocol: used to check if near user is valid
        :type omniaProtocol: OmniaProtocol instance
        :param min_rssi: minimum RSSI value, defaults to -70
        :type min_rssi: int, optional
        """

        ### OmniaProtocol ###
        self.omniaProtocol = omniaProtocol
        ### --- ###

        ### OmniaController ###
        self.omniaController = omniaController

        ### Proximity ###
        self.minimum_rssi = min_rssi
        self.last_near_user = ""
        ### --- ###

        ### Callback ###
        self.__callback = None
        ### --- ###

        ### Log ###
        self.log = logging.getLogger(
            '[{}]: OmniaBLE'.format(self.omniaProtocol.client_info["name"])
        )
        ### --- ###
    
    async def scanBLE(self, callback):
        """Starts receiving BLE from client

        :param callback: function called when a user is detected. "user_id" string passed as argument
        :type callback: function object
        """
        
        # __preCallback is passed because coordinates need to be pre processed
        self.omniaProtocol.registerReceiveCallback(self.__preCallback, OMT.READ_BLE)

        await self.omniaProtocol.send([ 1 ], OMT.READ_BLE)   # tell client to start reading touchscreen

    async def stopBLEScan(self):
        """Stops receiving BLE from client
        """

        self.__callback = None

        self.omniaProtocol.removeReceiveCallback(OMT.READ_BLE)

        await self.omniaProtocol.send([ 0 ], OMT.READ_BLE)   # tell client to stop reading touchscreen
    
    async def __preCallback(self, received_ble):
        """Preprocesses received BLE message from protocol

        :param received_ble: has this format: "<rssi>+<first_id>,<rssi>+<second_id>,..."
        :type received_ble: str
        """

        ble = ble.split(',')

        nearest_RSSI = -200     # out of range initial value
        nearest_user = ""

        if len(ble) >= 1:   # if at least one user is near
            for user in ble:
                user = user.split("+")  # split id and rssi
                
                if len(user) >= 2:  # if it's valid
                    rssi = int(user[0])
                    user_id = user[1]
                    
                    if self.omniaController.isValidUser(user_id):   # if this user is registered in Omnia
                        self.log.debug("detected user with id: '{!r}'".format(user_id))
                        
                        if rssi >= self.minimum_rssi:   # if user is near
                            self.log.debug("near user: '{!r}'".format(rssi))
                            
                            if rssi > nearest_RSSI:     # if the user is the nearest
                                nearest_RSSI = rssi
                                nearest_user = user_id
                                self.log.debug("NEAREST USER: '{!r}'".format(nearest_user))
            
            if nearest_user != "":
                self.last_near_user = nearest_user
                self.log.debug("DETECTED PROXIMITY: user_id='{!r}'".format(self.last_near_user))

                if self.__callback:
                    self.__callback(self.last_near_user)

# ---------------------------------------------------- #

class OmniaNFC:
    """Utilities for NDC interaction
    """

    def __init__(self, omniaProtocol, omniaController):
        """Initialization

        :param omniaProtocol: low-level OmniaProtocol
        :type omniaProtocol: OmniaProtocol instance
        :param omniaProtocol: used to check if near user is valid
        :type omniaProtocol: OmniaProtocol instance
        """

        ### OmniaProtocol ###
        self.omniaProtocol = omniaProtocol
        ### --- ###

        ### OmniaController ###
        self.omniaController = omniaController

        ### Proximity ###
        self.last_near_user = ""
        ### --- ###

        ### Callback ###
        self.__callback = None
        ### --- ###

        ### Log ###
        self.log = logging.getLogger(
            '[{}]: OmniaNFC'.format(self.omniaProtocol.client_info["name"])
        )
        ### --- ###
    
    async def setNFC(self, sclk, mosi, miso, rst, sda):
        """Sets NFC reader and wiring.

        :param sclk: SCLK pin (SPI)
        :type sclk: int
        :param mosi: MOSI pin (SPI)
        :type mosi: int
        :param miso: MISO pin (SPI)
        :type miso: int
        :param rst: RST pin (SPI)
        :type rst: int
        :param sda: SDA pin (SPI)
        :type sda: int
        """
        
        await self.omniaProtocol.send([
                sclk,
                mosi,
                miso,
                rst,
                sda
                ], OMT.SET_NFC)
    
    async def scanNFC(self, callback):
        """Starts receiving NFC from client

        :param callback: function called when a user is detected. "user_id" string passed as argument
        :type callback: function object
        """
        
        # __preCallback is passed because coordinates need to be pre processed
        self.omniaProtocol.registerReceiveCallback(self.__preCallback, OMT.READ_NFC)

        await self.omniaProtocol.send([ 1 ], OMT.READ_NFC)   # tell client to start reading touchscreen

    async def stopNFCScan(self):
        """Stops receiving NFC from client
        """

        self.__callback = None

        self.omniaProtocol.removeReceiveCallback(OMT.READ_NFC)

        await self.omniaProtocol.send([ 0 ], OMT.READ_NFC)   # tell client to stop reading touchscreen
    
    async def __preCallback(self, received_nfc):
        """Preprocesses received NFC message from protocol

        :param received_nfc: has this format: "<nfc_id>:"
        :type received_nfc: str
        """

        nfc = received_nfc.split(":")    # -> nfc = ["<nfc_id>", ""]
        
        if(len(nfc) >= 2):  # check if received nfc is valid
            
            nfc = nfc[1]
            if len(nfc) == 8:  # received nfc id is valid
                self.last_near_user = nfc
                self.is_near = True
                self.log.debug("DETECTED PROXIMITY: user_id='{!r}'".format(self.last_near_user))

                if self.__callback:
                    self.__callback(self.last_near_user)