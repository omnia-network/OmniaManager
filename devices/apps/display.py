from PIL import Image
import time
import json

### Omnia libraries ###
from modules.omniaUI                import OmniaUI, OmniaUIElement
from modules.omniaDisplay           import OmniaILI9341Display, OmniaTouchscreen
### --- ###

class Display:
    def __init__(self, username, omniaController):
        self.device = 0
        self.username = username
        self.omniaController = omniaController
        self.sharing = self.omniaController.OMS
        self.deviceChanged = True

        self.omniaProtocol = None

        self.omniaDisplay = None
        self.omniaTouchscreen = None

        self.width = 320
        self.height = 240
        self.ui = OmniaUI( (self.width, self.height), click_callback=self.clickCallback, debug=True )

        ## touch
        self.x = 0
        self.y = 0

        self.old_y = 0

        self.count = 0

        self.refresh_timeout = 1  # seconds
        self.time = time.time()

        self.volume = 5

        # UI elements
        self.song_time = None
        self.song_duration = None
        self.dot = None
        self.song_name = None
        self.cover = None
        self.text_volume = None

        with open("devices/resources/audio/playlist.json", "r") as p:
            self.playlist = json.load(p)
        
        self.pl_index = "0"
        
        # song parameters
        self.song_length = 1
        self.elapsed_seconds = 0
        self.pause = True

    def getNotificationMessage(self, deviceName, username=None):

        msg = []

        msg.append([(10, 35), deviceName.replace("_", " ").upper()])
        msg_status = "START STREAM?"
        
        msg.append([(10,50), msg_status])

        return msg
    
    async def handleStreaming(self, device):
        if self.device != device:
            #print("setting new device", self.device, device)
            if self.device != 0:
                await self.stop()
            old_device = self.device
            self.__setDevice(device)
            self.deviceChanged = True

            if old_device != 0:
                await old_device.resetStreamingUser()
    
    def __setDevice(self, device):
        self.device = device
        self.omniaProtocol = self.device.omniaProtocol

        self.omniaDisplay = OmniaILI9341Display(self.omniaProtocol, (self.width,self.height))
        self.omniaTouchscreen = OmniaTouchscreen(self.omniaProtocol, self.width, self.height)

    
    def touchCallback(self, xy_coordinates):

        self.x = xy_coordinates[0]
        self.y = xy_coordinates[1]
        self.ui.click((self.x, self.y))
    
    def clickCallback(self, button):
        #button.setText("count")
        #self.count += 1
        if button.id == "play":
            button.visible = False
            pause = self.ui.getElement("pause")
            pause.visible = True
            self.pause = False
            self.sharing.setAttribute(self.username, "pause", False)
        elif button.id == "pause":
            button.visible = False
            play = self.ui.getElement("play")
            play.visible = True
            self.pause = True
            self.sharing.setAttribute(self.username, "pause", True)
        
        elif button.id == "prev":
            self.elapsed_seconds = 0
                
            self.sharing.setAttribute(self.username, "prev", True)

            x = int(self.elapsed_seconds * ((self.width - 18)/self.song_length))
            self.dot.setPosition((x,175))

            self.ui.refresh_image()

        elif button.id == "next":
            self.elapsed_seconds = 0
                
            self.sharing.setAttribute(self.username, "next", True)

            x = int(self.elapsed_seconds * ((self.width - 18)/self.song_length))
            self.dot.setPosition((x,175))

            self.ui.refresh_image()
        
        elif button.id == "vup":
            if self.volume < 10:
                self.volume += 1
                self.text_volume.setText(str(self.volume))
                self.sharing.setAttribute( self.username, "volume", self.volume)

        elif button.id == "vdown":
            if self.volume > 0:
                self.volume -= 1
                self.text_volume.setText(str(self.volume))
                self.sharing.setAttribute( self.username, "volume", self.volume)

        #self.label.setText("count: "+str(self.count))
        self.ui.refresh_image()
        print("button '{}' clicked".format(button.id))

    async def send_img(self):
        img = self.ui.get_image()
        img=img.convert("RGB")
        #img.rotate(90, expand=True)

        self.omniaDisplay.setImage(img)
        await self.omniaDisplay.sendDisplay()

    def setSongInfo(self):
        self.song_title = self.playlist[self.pl_index]["name"]
        self.song_author = self.playlist[self.pl_index]["author"]
        self.song_cover = self.playlist[self.pl_index]["cover"]

        self.song_name.setText(self.song_title+" - "+self.song_author)

        img = Image.open(self.song_cover)
        img = img.convert("RGBA")
        img = img.resize((160,160))
        self.cover.addImage(img)

    async def start(self):
        await self.omniaTouchscreen.startReadingTouchscreen(self.touchCallback)
        
        self.ui.clear_image()
        self.ui.loadFromXMLFile("devices/resources/ui/home.xml")

        self.song_time = self.ui.getElement("song-time")
        self.song_duration = self.ui.getElement("song-duration")
        self.dot = self.ui.getElement("circle")

        self.song_name = self.ui.getElement("song-name")
        self.cover = self.ui.getElement("cover")

        self.text_volume = self.ui.getElement("vlevel")

        x = int(self.elapsed_seconds * ((self.width - 18)/self.song_length))
        self.dot.setPosition((x,175))       

        self.setSongInfo()

        await self.send_img()

        self.time = time.time()
    
    async def stop(self):
        await self.omniaTouchscreen.stopReadingTouchscreen()
        self.ui.clear_image()
        await self.send_img()  

    async def run(self):

        if self.device:

            await self.send_img()

            if time.time() - self.time > self.refresh_timeout:
                self.time = time.time()

                index = self.sharing.getAttribute(self.username, "song_id")
                if index:
                    if index != self.pl_index:
                        self.pl_index = index
                        self.setSongInfo()

                # display song lenght
                self.song_length = self.sharing.getAttribute(self.username, "duration")
                if self.song_length:
                    duration = "{}:{:02}".format( int(self.song_length) // 60, int(self.song_length) % 60 )
                    self.song_duration.setText(duration)
                else:
                    self.song_length = 1

                self.elapsed_seconds = self.sharing.getAttribute(self.username, "elapsed_time")
                if not self.elapsed_seconds:
                    self.elapsed_seconds = 0
                
                if not self.pause:
                    self.song_time.setText("{}:{:02}".format(int(self.elapsed_seconds) // 60, int(self.elapsed_seconds) % 60))
                    
                    x = int(self.elapsed_seconds * ((self.width - 18)/self.song_length))
                    self.dot.setPosition((x,175))

                self.ui.refresh_image()
                await self.send_img()

    