from PIL import Image, ImageDraw, ImageFont
import logging
import time
import xml.etree.ElementTree as ET
from ast import literal_eval as make_tuple

class OmniaUI:

    default_font = ImageFont.truetype("fonts/Arial.ttf", 20)

    def __init__(self, display_dimensions, click_callback=None, click_bias=0, background_color=(255,255,255), background_image=None, font=None, debug=False):

        # Dimensions
        self.width = display_dimensions[0]
        self.height = display_dimensions[1]

        # Touch
        self.touch_x = 0
        self.touch_y = 0
        self.bias = click_bias
        self.click_callback = click_callback

        # Image utilities
        self.image = Image.new("RGBA", (self.width, self.height), background_color)
        self.draw = ImageDraw.Draw(self.image)
        
        self.orientation = "landscape"

        if self.width < self.height:
            self.orientation = "portrait"

        # Colors
        self.background_color = background_color

        # Background Image
        self.background_image = background_image

        # Font
        self.font = self.default_font
        if font:
            self.font = font

        # Elements
        self.buttons = {}
        self.labels = {}
        self.lines = {}
        
        # Debug
        self.debug = debug
        self.debug_point = None
        self.debug_point_time = time.time()

        # XML
        #self.tree = None
        self.root = None

        ### Logging ###
        logging.getLogger("PIL").setLevel(logging.WARNING)
        self.log = logging.getLogger('OmniaUI')
        ### --- ###
    
    def _draw_debug_point(self):
        self.draw.ellipse(self.debug_point, fill=(255,0,0))

    def click(self, coordinates):
        x = coordinates[0]
        y = coordinates[1]
        if (0 <= x <= self.width) and (0 <= y <= self.height):
            self.touch_x = x
            self.touch_y = y

            # draw a red point of radius = r and center = (x,y)
            if self.debug:
                r = 5
                self.debug_point = [(x-r, y-r), (x+r, y+r)]
                #self._draw_debug_point()
            
            for button_id in self.buttons:
                button = self.buttons[button_id]

                if button.isClicked(coordinates, self.bias):
                    self.log.debug("Element '{}' clicked".format(button.id))
                    
                    if self.click_callback:
                        self.click_callback(button)
                        break
                    else:
                        return button
        else:
            #raise ValueError("Click coordinates '{}' outside image".format((x,y)))
            self.log.error("Click coordinates '{}' outside image".format((x,y)))
    
    ### ELEMENTS ###

    def _draw_element(self, element):
        if element.visible:
            if element.type == "line":
                self.draw.line(element.getXY(), fill=element.color, width=element.width)
            else:
                if element.image:
                    self.image.paste(element.image, element.box[0], mask=element.image)
                else:
                    if element.outline_color:
                        self.draw.rectangle(element.box, fill=element.background_color, outline=element.outline_color)

                    self.draw.text(( element.x0 + element.padding, element.y0 + element.padding ), element.text, fill=element.text_color, font=element.font)

    def addElement(self, element):
        element_id = element.id
        element_type = element.type

        if element_type == "button":
            
            if not element_id in self.buttons:
                # register button
                self.buttons[element_id] = element

                # draw button
                self._draw_element(element)
            
            else:
                #raise ValueError("Button with id '{}' already exists".format(element_id))
                self.log.error("Button with id '{}' already exists".format(element_id))
        
        elif element_type == "label":
            
            if not element_id in self.labels:
                # register label
                self.labels[element_id] = element

                # draw label
                self._draw_element(element)
        
            else:
                #raise ValueError("Label with id '{}' already exists".format(element_id))
                self.log.error("Label with id '{}' already exists".format(element_id))

        elif element_type == "line":
            
            if not element_id in self.lines:
                # register line
                self.lines[element_id] = element

                # draw line
                self._draw_element(element)
        
            else:
                #raise ValueError("Line with id '{}' already exists".format(element_id))
                self.log.error("Line with id '{}' already exists".format(element_id))

    def removeElement(self, element_id):
        if element_id in self.buttons:
            self.buttons.pop(element_id)
            self.refresh_image()
        elif element_id in self.labels:
            self.labels.pop(element_id)
            self.refresh_image()
        elif element_id in self.lines:
            self.labels.pop(element_id)
            self.refresh_image()
        else:
            #raise ValueError("Element with id '{}' does not exist".format(element_id))
            self.log.error("Element with id '{}' does not exist".format(element_id))
    
    def getElement(self, elem_id):
        if elem_id in self.buttons:
            return self.buttons[elem_id]
        elif elem_id in self.labels:
            return self.labels[elem_id]
        elif elem_id in self.lines:
            return self.lines[elem_id]
        
    def updateElement(self, element):
        element_id = element.id
        element_type = element.type

        if element_type == "button":
            
            if element_id in self.buttons:
                # register button
                self.buttons[element_id] = element

                # draw button
                self._draw_element(element)
            
            else:
                #raise ValueError("Button with id '{}' does not exist".format(element_id))
                self.log.error("Button with id '{}' does not exist".format(element_id))
        
        elif element_type == "label":
            
            if element_id in self.labels:
                # register label
                self.labels[element_id] = element

                # draw label
                self._draw_element(element)
        
            else:
                #raise ValueError("Label with id '{}' does not exist".format(element_id))
                self.log.error("Label with id '{}' does not exist".format(element_id))
        
        elif element_type == "label":
            
            if element_id in self.lines:
                # register label
                self.lines[element_id] = element

                # draw label
                self._draw_element(element)
        
            else:
                #raise ValueError("Line with id '{}' does not exist".format(element_id))
                self.log.error("Line with id '{}' does not exist".format(element_id))
        
        self.refresh_image()

    ### --- ###

    ### IMAGE ###

    def refresh_image(self):
        self.clear_image()
        for button_id in self.buttons:
            self._draw_element(self.buttons[button_id])
        
        for label_id in self.labels:
            self._draw_element(self.labels[label_id])
        
        for line_id in self.lines:
            self._draw_element(self.lines[line_id])
        
        if self.debug:
            if self.debug_point:
                self._draw_debug_point()

    def show_image(self):
        self.image.show()
    
    def clear_image(self, box=None):
        if not box:
            box = [0,0,self.width,self.height]
            #print(box)
        
        if self.background_image:
            self.image.paste(self.background_image, box)
        else:
            self.image.paste(self.background_color, box)
    
    def reset_image(self):
        self.buttons = {}
        self.labels = {}
        self.lines = {}
        self.background_image = None
        self.background_color = (255,255,255)

    def get_image(self):
        return self.image.copy()
    
    def refresh_and_get_image(self):
        self.refresh_image()
        return self.image.copy()
    
    def _invert_dimensions(self):
        old_width = self.width
        self.width = self.height
        self.height = old_width

        self.image = self.image.resize((self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)

    def changeOrientation(self):
        if self.orientation == "portrait":
            self.orientation = "landscape"
                
        elif self.orientation == "landscape":
            self.orientation = "portrait"
        
        self._invert_dimensions()

        if self.background_image:
            #self.background_image = self.background_image.rotate(self.rotation, expand=True)
            self.background_image = self.background_image.resize((self.width, self.height))

        #print(self.width, self.height)
        self.refresh_image()
    
    def getOrientation(self):
        return self.orientation

    ### --- ###

    ### COLORS ###

    def setBackgroundImage(self, image):
        image = image.resize((self.width, self.height))

        self.background_image = image
        self.refresh_image()
    
    def setBackgroundColor(self, color):
        self.background_color = color
        self.refresh_image()

    ### --- ###

    ### XML ###

    def loadFromXMLFile(self, filename):
        tree = ET.parse(filename)
        self.root = tree.getroot()
        self._load_xml()
    
    def loadFromXML(self, xml_string):
        self.root = ET.fromstring(xml_string)
        self._load_xml()

    def _load_xml(self):
        self.reset_image()

        if "dimensions" in self.root.attrib:
            dim = make_tuple(self.root.attrib["dimensions"])
            self.width = dim[0]
            self.height = dim[1]
            self.image = Image.new("RGBA", (self.width, self.height), self.background_color)
            self.draw = ImageDraw.Draw(self.image)
        
        if "orientation" in self.root.attrib:
            self.orientation = self.root.attrib["orientation"]

            #print(self.orientation, self.width, self.height)

            if self.orientation == "landscape" and self.width < self.height:
                self._invert_dimensions()
            elif self.orientation == "portrait" and self.width >= self.height:
                self._invert_dimensions()

        if "bg-color" in self.root.attrib:
            self.background_color = make_tuple(self.root.attrib["bg-color"])

        if "bg-image" in self.root.attrib:
            img = Image.open(self.root.attrib["bg-image"])
            img = img.convert("RGBA")
            img = img.resize((self.width, self.height))
            self.background_image = img

        for child in self.root:
            elem_id = child.attrib['id']
            elem_type = child.tag
            elem = {}
            for sub_child in child:
                if sub_child.text:
                    if sub_child.tag == "image" and "dimensions" in sub_child.attrib:
                        elem[sub_child.tag] = {"text": sub_child.text, "dimensions": make_tuple(sub_child.attrib["dimensions"])}
                    else:
                        elem[sub_child.tag] = sub_child.text
            
            #print(elem)
            
            if len(elem) > 0:
                if elem_type == "line":
                    if "start" in elem:
                        start = elem["start"]
                        start = make_tuple(start)
                    else:
                        #raise ValueError("Start property is required (not found in element with id: '{}')".format(elem_id))
                        self.log.error("Start property is required (not found in element with id: '{}')".format(elem_id))
                    
                    if "end" in elem:
                        end = elem["end"]
                        end = make_tuple(end)
                    else:
                        #raise ValueError("End property is required (not found in element with id: '{}')".format(elem_id))
                        self.log.error("End property is required (not found in element with id: '{}')".format(elem_id))
                    
                    #print(start, end)
                    line_element = OmniaUILine(elem_id, [start, end])

                    if "width" in elem:
                        width = int(elem["width"])
                        line_element.setWidth(width)
                    
                    if "color" in elem:
                        color = elem["color"]
                        color = make_tuple(color)
                        line_element.setColor(color)
                    
                    if "visible" in elem:
                        visible = elem["visible"]
                        if visible in ['true', 'True', '1']:
                            line_element.visible = True
                        elif visible in ['false', 'False', '0']:
                            line_element.visible = False
                    
                    self.addElement(line_element)

                else:
                    if "position" in elem:
                        position = elem["position"]
                        position = make_tuple(position)
                    else:
                        #raise ValueError("Position property is required (not found in element with id: '{}')".format(elem_id))
                        self.log.error("Position property is required (not found in element with id: '{}')".format(elem_id))
                    
                    
                    if "text" in elem:
                        text = elem["text"]
                    else:
                        #raise ValueError("Text property is required (not found in element with id: '{}')".format(elem_id))
                        self.log.error("Text property is required (not found in element with id: '{}')".format(elem_id))

                    ui_element = OmniaUIElement(elem_id, elem_type, position, text)

                    if elem_type == "button":
                        ui_element.clickable = True

                    if "image" in elem:
                        image = elem["image"]
                        if "text" in image:
                            img = Image.open(image["text"])
                            img = img.convert("RGBA")
                            img = img.resize(image["dimensions"])
                            ui_element.addImage(img)
                    
                    
                    if "visible" in elem:
                        visible = elem["visible"]
                        if visible in ['true', 'True', '1']:
                            ui_element.visible = True
                        elif visible in ['false', 'False', '0']:
                            ui_element.visible = False

                    
                    if "dimensions" in elem:
                        dimensions = elem["dimensions"]
                        dimensions = make_tuple(dimensions)
                        ui_element.setDimensions(dimensions)

                    if "text-color" in elem:
                        text_color = elem["text-color"]
                        text_color = make_tuple(text_color)
                        ui_element.setTextColor(text_color)

                    if "background-color" in elem:
                        background_color = elem["background-color"]
                        background_color = make_tuple(background_color)
                        ui_element.setBackgroundColor(background_color)
                    
                    if "outline-color" in elem:
                        outline_color = elem["outline-color"]
                        outline_color = make_tuple(outline_color)
                        ui_element.setOutlineColor(outline_color)
                    
                    if "font-size" in elem:
                        font_size = int(elem["font-size"])
                        ui_element.setFontSize(font_size)
                    
                    if "padding" in elem:
                        padding = int(elem["padding"])
                        ui_element.setPadding(padding)
                    
                    self.addElement(ui_element)
        
        self.refresh_image()

    ### --- ###

class OmniaUIElement:

    def __init__(self, id, element_type, position, text, image=None, clickable=False, visible=True, dimensions=(70,30), text_color=(0,0,0), font_name="fonts/Arial.ttf", font_size=20, padding=5, background_color=None, outline_color=None):

        # Id
        self.id = id

        # Type
        self.type = element_type
        
        # Font
        self.font_size = font_size
        self.font_name = font_name
        
        self.font = ImageFont.truetype(self.font_name, self.font_size)
        
        # Padding
        self.padding = padding

        # Text
        self.text = text

        # Coordinates and box
        self.dimensions = dimensions

        if text != '':
            text_size = self.font.getsize(text)
            self.dimensions = ( text_size[0], text_size[1] )
        
        self.x0 = position[0]
        self.y0 = position[1]

        self.x1 = 0
        self.y1 = 0

        self.box = []

        # Visible
        self.visible = visible

        # Colors
        self.text_color = text_color
        self.background_color = background_color
        self.outline_color = outline_color

        # Image
        self.image = image
        if self.image:
            self.dimensions = self.image.size
        
        # Click
        self.clickable = clickable

        # set initial box
        self._update_box()
    
    def isClicked(self, coordinates, bias):
        x = coordinates[0]
        y = coordinates[1]

        if (self.x0 - bias <= x <= self.x1 + bias) and (self.y0 - bias <= y <= self.y1 + bias) and self.clickable and self.visible:
            return True
        else:
            return False

    def _update_box(self):
        self.x1 = self.x0 + self.dimensions[0]
        self.y1 = self.y0 + self.dimensions[1]

        # add margin for text
        if not self.image:
            self.x1 += 2*self.padding
            self.y1 += 2*self.padding
        
        self.box = [( self.x0, self.y0 ), ( self.x1, self.y1 )]

    def setText(self, text):
        self.text = text
        text_size = self.font.getsize(text)
        self.dimensions = ( text_size[0], text_size[1] )

        self._update_box()
    
    def setPosition(self, position):
        self.x0 = position[0]
        self.y0 = position[1]

        self._update_box()
    
    def getPosition(self):
        return (self.x0, self.y0)
    
    def setDimensions(self, dimensions):
        self.dimensions = dimensions

        self._update_box()
    
    def setBackgroundColor(self, color):
        self.background_color = color

    def setOutlineColor(self, color):
        self.outline_color = color
    
    def setTextColor(self, color):
        self.text_color = color
    
    def addImage(self, image):
        self.dimensions = image.size
        self.image = image

        self._update_box()

    def removeImage(self):
        self.image = None

    def setFont(self, font):
        self.font = font
    
    def getFont(self):
        return self.font
    
    def setFontName(self, font_name):
        self.font_name = font_name
        self.font = ImageFont.truetype(self.font_name, self.font_size)
    
    def getFontName(self):
        return self.font_name

    def setFontSize(self, font_size):
        self.font_size = font_size
        self.font = ImageFont.truetype(self.font_name, self.font_size)
    
    def getFontSize(self):
        return self.font_size
    
    def setPadding(self, padding):
        self.padding = padding

class OmniaUILine:

    def __init__(self, line_id, xy, width=1, color=(0,0,0), visible=True):

        self.id = line_id

        self.lx0 = xy[0][0]
        self.ly0 = xy[0][1]

        self.lx1 = xy[1][0]
        self.ly1 = xy[1][1]

        self.width = width

        self.color = color

        self.visible = visible

        self.type = "line"
    
    def setXY(self, xy):
        self.lx0 = xy[0][0]
        self.ly0 = xy[0][1]

        self.lx1 = xy[1][0]
        self.ly1 = xy[1][1]
    
    def getXY(self):
        return [(self.lx0, self.ly0), (self.lx1, self.ly1)]
    
    def setWidth(self, width):
        self.width = width
    
    def getWidth(self):
        return self.width
    
    def setColor(self, color):
        self.color = color
    
    def getColor(self):
        return self.color