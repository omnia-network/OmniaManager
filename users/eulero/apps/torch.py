import curio

class Torch:
   
    def __init__(self, username, omnia1BitDisplay, omniaPins, omniaController):
        self.username = username

        ### Omnia libraries
        self.omnia1BitDisplay = omnia1BitDisplay
        self.omniaPins = omniaPins
        self.omniaController = omniaController
        ### --- ###
        
        self.ledstatus = False

        self.changed = True
        self.close_app = False

        self.i = 0
        self.j = 0

        self.color_picker = False
        self.second_column = False

        self.red = 0
        self.green = 0
        self.blue = 0
    
    async def clickCallback(self, clickedBtn):
        if(clickedBtn == "SELECT"):
            if self.color_picker:
                if self.second_column:
                    self.second_column = False
                    await self.omniaPins.setNeopixelPin("NEO1", [self.red, self.green, self.blue])
                else:
                    if self.j==3: # RESET
                        self.red = 0
                        self.green = 0
                        self.blue = 0
                        await self.omniaPins.setNeopixelPin("NEO1", [self.red, self.green, self.blue])
                    elif self.j==4:
                        self.color_picker = False
                        self.j=0
                    else:
                        self.second_column = True
            else:
                if(self.i==2):
                    self.close_app=True
                elif(self.i==1):
                    self.ledstatus = not self.ledstatus
                    await self.omniaPins.setOutPin("LED", self.ledstatus)
                elif(self.i==0):
                    self.color_picker = True

            self.changed = True
        
        elif(clickedBtn == "DOWN"):
            if self.color_picker:
                if self.second_column:
                    if self.j==0:
                        if self.red > 0:
                            self.red -= 5
                    if self.j==1:
                        if self.green > 0:
                            self.green -= 5
                    if self.j==2:
                        if self.blue > 0:
                            self.blue -= 5
                else:
                    if self.j==4:
                        self.j=0
                    else:
                        self.j+=1
            else:
                if self.i==2:
                    self.i=0
                else:
                    self.i+=1

            self.changed = True
                
        elif(clickedBtn == "UP"):
            if self.color_picker:
                if self.second_column:
                    if self.j==0:
                        if self.red < 255:
                            self.red += 5
                    if self.j==1:
                        if self.green < 255:
                            self.green += 5
                    if self.j==2:
                        if self.blue < 255:
                            self.blue += 5
                else:
                    if self.j==0:
                        self.j = 4
                    else:
                        self.j -= 1
            else:
                if self.i==0:
                    self.i=2
                else:
                    self.i-=1

            self.changed = True

    async def run(self):

        self.omniaPins.registerInputCallback(self.clickCallback)

        self.changed = True		
        
        self.color_picker = False
        self.second_column = False

        while not self.close_app:
            if (self.changed):
                    self.changed=False
                    self.omnia1BitDisplay.resetImage()
                    if not self.color_picker:
                        self.omnia1BitDisplay.image_draw.text((45,0), "TORCH ", 255,self.omnia1BitDisplay.FONT_ARIAL_11)
                        self.omnia1BitDisplay.image_draw.text((10,10),"TOP ", 255,self.omnia1BitDisplay.FONT_ARIAL_11)
                        self.omnia1BitDisplay.image_draw.text((10,20),"SIDE ", 255,self.omnia1BitDisplay.FONT_ARIAL_11)
                        self.omnia1BitDisplay.image_draw.text((10,30),"MENU ", 255,self.omnia1BitDisplay.FONT_ARIAL_11)
                        self.omnia1BitDisplay.image_draw.text((1,10+self.i*10),">", 255,self.omnia1BitDisplay.FONT_ARIAL_11)
                    else:
                        self.omnia1BitDisplay.image_draw.text((10,0),"RED ", 255,self.omnia1BitDisplay.FONT_ARIAL_11)
                        self.omnia1BitDisplay.image_draw.text((70,0),str(self.red), 255,self.omnia1BitDisplay.FONT_ARIAL_11)

                        self.omnia1BitDisplay.image_draw.text((10,10),"GREEN ", 255,self.omnia1BitDisplay.FONT_ARIAL_11)
                        self.omnia1BitDisplay.image_draw.text((70,10),str(self.green), 255,self.omnia1BitDisplay.FONT_ARIAL_11)

                        self.omnia1BitDisplay.image_draw.text((10,20),"BLUE ", 255,self.omnia1BitDisplay.FONT_ARIAL_11)
                        self.omnia1BitDisplay.image_draw.text((70,20),str(self.blue), 255,self.omnia1BitDisplay.FONT_ARIAL_11)

                        self.omnia1BitDisplay.image_draw.text((10,30),"RESET ", 255,self.omnia1BitDisplay.FONT_ARIAL_11)
                        self.omnia1BitDisplay.image_draw.text((10,40),"BACK ", 255,self.omnia1BitDisplay.FONT_ARIAL_11)

                        if self.second_column:
                            self.omnia1BitDisplay.image_draw.text((60,self.j*10),">", 255,self.omnia1BitDisplay.FONT_ARIAL_11)
                        else:
                            self.omnia1BitDisplay.image_draw.text((1,self.j*10),">", 255,self.omnia1BitDisplay.FONT_ARIAL_11)

                    await self.omnia1BitDisplay.sendDisplay()
        
            await curio.sleep(0.1)

        self.close_app = False
        return -1


