import logging

class OmniaMediaSharing:
    """Handles a dictionary where objects to be shared are stored
    """

    def __init__(self):
        self.contents = {}

        '''
        contents = {
            "username": {
                "text": "sometext",
                "image": "someimage",
                ...
            },
            "another_username":{
                ...
            },
            ...
        }
        '''

        ### Logging ###
        self.log = logging.getLogger('OmniaMediaSharing')
        ### --- ###
    
    def getText(self, username):
        if username in self.contents:
            return self.contents[username]["text"]
        
        return ''
    
    def setText(self, text, username):
        if username in self.contents:
            self.contents[username]["text"] = text
        else:
            self.contents.__setitem__(username, {"text": text})
    
    def addToText(self, text, username):
        if username in self.contents and "text" in self.contents[username]:
            self.contents[username]["text"] += text
        else:
            self.setText(text, username)
        
        print(self.contents[username]["text"])
    
    def removeFromText(self, nChar, username):
        if username in self.contents:
            if "text" in self.contents[username]:
                self.contents[username]["text"] = self.contents[username]["text"][:-nChar]

    def setAttribute(self, username, attribute, value=''):
        """Sets object to share

        :param username: user under which to save the object
        :type username: str
        :param attribute: object name
        :type attribute: str
        :param value: object (can be a string, number, class object, ...), defaults to ''
        :type value: str or int or object or ..., optional
        """
        if username in self.contents:
            self.contents[username][attribute] = value
        else:
            self.contents.__setitem__(username, {attribute: value})
    
    def getAttribute(self, username, attribute):
        """Gets object at that attribute for this username

        :param username: user under which to search for the attribute
        :type username: str
        :param attribute: name of the object to search for
        :type attribute: str
        :return: object if found at that attribute, None otherwise
        :rtype: str or int or object or ...
        """
        if username in self.contents:
            if attribute in self.contents[username]:
                return self.contents[username][attribute]
            else:
                self.log.warning("Attribute '{}' not found for user '{}'".format(attribute, username))
                return None
        else:
            self.log.warning("User '{}' not found".format(username))