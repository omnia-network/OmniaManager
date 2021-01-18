from PIL   			            import Image
import os
import importlib
import curio
import logging

### Omnia libraries ###
from core.omniaProtocol             import OmniaProtocol

from manager.notifyService          import NotifyService

from modules.omniaDisplay           import Omnia1BitDisplay
from modules.omniaIO                import OmniaPins
### --- ###

class User:

    def __init__(self, socket, address, user_data, omniaController=None):

        ### Socket ###
        self.socket = socket
        self.address = address          # (IPAddress, Port)
        ### --- ###

        ### User Data ###
        '''
        user_data structure
        {
            "name": "user_name",
            "uid": "user id"    # RFID or BLE
        }
        '''
        self.user_data = user_data
        self.user_data["type"] = "user"
        self.name = user_data["name"]   # user name
        ### --- ###

        ### Omnia Protocol ###
        self.omniaProtocol = OmniaProtocol(self.socket, self.user_data)
        ### --- ###

        ### Omnia Controller ###
        self.omniaController = omniaController
        ### --- ###

        ### OmniaDisplay and OmniaPins ###
        self.omnia1BitDisplay = Omnia1BitDisplay(self.omniaProtocol, (128,64))
        self.omniaPins = OmniaPins(self.omniaProtocol)
        ### --- ###

        ### Applications ###
        self.applications = []       # list of apps objects
        self.applications_name = []  # list of apps names
        ### --- ###

        ### Logging ###
        logging.getLogger("PIL").setLevel(logging.WARNING)  # disable PIL library logging
        self.log = logging.getLogger(
            "[{}_{}_{}]: main".format(self.name, *self.address)
        )
        ### --- ###

    # get initial configuration of pins and settings
    async def initConfig(self):
        # initialize pins
        await self.omniaPins.loadPinoutFromJSON("users/" + self.name + "/config/pinout.json")

        # initialize display
        await self.omnia1BitDisplay.setDisplayFromJSON("users/" + self.name + "/config/display.json")
        self.omnia1BitDisplay.loadConfigFromJSON("users/" + self.name + "/config/config.json")

    # watch startup
    async def initConnection(self):    
        # send user profile pic
        pic = Image.open("users/" + self.name + "/resources/images/pic.png")
        self.omnia1BitDisplay.setImage(pic)
        await self.omnia1BitDisplay.sendDisplay()
        
        await curio.sleep(3)

        # send Omnia version
        self.omnia1BitDisplay.resetImage()
        self.omnia1BitDisplay.image_draw.text( (10,0), "OMNIA", 255, self.omnia1BitDisplay.FONT_ARIAL_30)
        self.omnia1BitDisplay.image_draw.text( (18,32), "V "+ self.omniaProtocol.getVersion(), 255, self.omnia1BitDisplay.FONT_ARIAL_30)
        
        await self.omnia1BitDisplay.sendDisplay()
        # await curio.sleep(3)

        self.prepareApps()
    
    def prepareApps(self):

        userAppsPath = "users/" + self.name + "/apps"    # path to user apps

        # create list of files in src's user path
        apps = next(os.walk(userAppsPath))[2]
        apps.sort()     # sort in alphabetical order

        for app in apps:
            app_name = app[:-3]     # remove .py extension
            if app_name[0] != "_":      # do not import apps that start with "_"
                self.log.debug("loading app: {!r}".format(app_name.upper()))
                AppObj = getattr(importlib.import_module("users." + self.name + ".apps." + app_name), app_name.capitalize())    # import App class
                self.applications.append(AppObj(self.name, self.omnia1BitDisplay, self.omniaPins, self.omniaController))      # create App instance
                self.applications_name.append(app_name.upper())     # append app name
            else:
                self.log.debug("ignoring app: {!r}".format(app_name[1:].upper()))

    async def runApps(self):
        await curio.sleep(6)
        self.log.debug("loading MENU")
        Menu = getattr(importlib.import_module("users." + self.name + ".menu"), "Menu")  # import Menu class
        menu = Menu(self.applications_name, self.omnia1BitDisplay, self.omniaPins, self.omniaController)    # create Menu instance
        
        i = 0   # index of app to run (-1 = Menu) from self.applications list
        self.log.debug("starting app: {!r}".format(self.applications_name[i]))

        while True:
            if i == -1:
                self.log.debug("starting MENU")
                i = await menu.run()    # start menu and finally get selected app index
                self.log.debug("exited MENU")
                self.log.debug("starting app: {!r}".format(self.applications_name[i]))
            else:
                running_app = self.applications_name[i]     # currently running app
                i = await self.applications[i].run()    # start app and finally get selected app index
                self.log.debug("exited {!r}".format(running_app))
                if i != -1:
                    self.log.debug("starting app: {!r}".format(self.applications_name[i]))

    async def main(self):
        
        # initialize configuration of pins and settings
        _ = await self.omniaProtocol.addTask(self.initConfig, wait_for_execution=True)

        # run initConnection as a task
        _ = await self.omniaProtocol.addTask(self.initConnection, wait_for_execution=True)

        ### Notification ###
        notifyService = NotifyService(self.name, self.omnia1BitDisplay, self.omniaPins, self.omniaController)   # create NotifyService instance
        _ = await self.omniaProtocol.addTask(notifyService.run)     # create task to run the notify service
        ### --- ###

        ## run omniaProtocol with loop
        await self.omniaProtocol.begin(self.runApps)
    
    async def resumeSocket(self, new_socket):
        await self.omniaProtocol.resumeSocket(new_socket)

        # initialize configuration of pins and settings
        _ = await self.omniaProtocol.addTask(self.initConfig, wait_for_execution=True)

        await self.omnia1BitDisplay.sendDisplay(force_send=True)    # send display to complete resumes

        self.log.debug("resumed")
        
    async def resumeEventListener(self, event):

        await event.wait()

        return self

