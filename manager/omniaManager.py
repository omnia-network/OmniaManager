from curio      import run, tcp_server, spawn, Event, sleep
import logging
import json
import sys
from curio.debug import logcrash

### Omnia libraries ###
from manager.device 			import Device
from manager.omniaController 	import OmniaController
from manager.user				import User
### --- ###

logging.basicConfig(
            level=logging.DEBUG,
            format='%(name)s: %(message)s',
            stream=sys.stderr,
        )

class OmniaManager:

    def __init__(self, ip_address, port, users_json_path, devices_json_path, authorizations_json_path):
        """Users and devices manager

        :param ip_address: manager ip address
        :type ip_address: str
        :param port: manager port
        :type port: int
        :param users_json_path: registered users. JSON file must have this structure:
                                {
                                    "mac-address":{     # mac address of the user's watch
                                        "name": "user_name",
                                        "uid": "user id"    # RFID or BLE 
                                    }
                                }
        :type users_json_path: str
        :param devices_json_path: registered devices. JSON file must have this structure:
                                {
                                    "mac-address":{     # mac address of the device
                                        "name": "device name",
                                        "class": "type of device"    # one of the applications in src/iot_funct folder
                                    }
                                }
        :type devices_json_path: str
        :param authorizations_path: path to JSON file containing authorizations. 
                                    Must have this structure:
                                    {
                                        "username1": ["device1", "device2", ... ],  # devices username1 can use
                                        "username2": ["device1", "device2", ... ],  # devices username2 can use
                                        ...
                                    }
        :type authorizations_path: str
        """
        
        with open(users_json_path, "r") as j:
            self.users = json.load(j)
        
        with open(devices_json_path, "r") as j:
            self.devices = json.load(j)
        
        ### Manager IP and Port
        self.ip_address = ip_address
        self.port = port
        ### --- ###

        ### OmniaController ###
        self.omniaController = OmniaController(authorizations_json_path)
        ### --- ###

        ### Tasks ###
        """TASKS structure
            {
                "client_mac1": {
                    "task": <client_task1>,
                    "resume_event": <event set when resuming>,
                    "resume_class": <client's class>    # added only after event has fired
                },
                "client_mac2": {
                    <same as above>
                },
                ...
            }
        """
        self.tasks = {}
        ### --- ###

        ### Logging ###
        self.log = logging.getLogger(
            "OmniaManager"
        )
        ### --- ###
    
    def startManager(self):
        """Create TCP server at the given address, handle connection with curio
        """
        self.log.info("STARTED")      # here we go :)
        run(tcp_server, self.ip_address, self.port, self.clientConnectedCb, with_monitor=True, debug=logcrash)
    
    async def clientConnectedCb(self, client_socket, client_address):
        """Handle client connected to manager

        :param client_socket: curio opened socket
        :type client_socket: socket object
        :param client_address: ("ip_address", port) of the client
        :type client_address: tuple
        """
        self.log.debug("----NEW CONNECTION----")
        self.log.debug("Address: {}".format(client_address))

        client_socket = client_socket.as_stream()   # use curio's SocketStream class

        client_mac = await client_socket.read_exactly(12)   # recv client's mac for identification

        '''if ':' in client_mac:
            client_mac.replace(':','')'''
        client_mac = client_mac.decode()

        self.log.debug("MAC address: {}".format(client_mac))
        
        previous_client_task = None
        if client_mac in self.tasks:    # if client had already connected before
            previous_client_task = self.tasks[client_mac]["task"]

        if previous_client_task and not previous_client_task.terminated:    # if client's task was not terminated for some reason
            
            ### log ###
            if client_mac in self.users:
                self.log.debug("resuming USER: {!r}".format(self.users[client_mac]["name"]))
            elif client_mac in self.devices:
                self.log.debug("resuming DEVICE: {!r}".format(self.devices[client_mac]["name"]))
            ### end log ###

            client_event = self.tasks[client_mac]["resume_event"]   # get resuming event
            await client_event.set()    # tell client we need a resume
            await sleep(1)  # wait for safe
            
            client_class = self.tasks[client_mac]["resume_class"] # get client_class returned by resumeEventListener
            
            await self.runClient(client_mac, client_class, client_socket)

        else:   # client had never connected before
            client_class = None     # client class to be instanciated (User or Device)

            # create a task for every client connected
            if client_mac in self.users:     # client is a user
                user_data = self.users[client_mac]    # get user data at this mac
                user_name = user_data["name"]

                self.log.debug("connecting USER: {!r}".format(user_name))
                
                # create a User class instance for this user
                client_class = User(client_socket, client_address, user_data, self.omniaController)
                self.omniaController.addUser(user_data)            

            elif client_mac in self.devices: # client is a device
                device_data = self.devices[client_mac]    # get device data at this mac
                device_name = device_data["name"]
                
                self.log.debug("connecting DEVICE: {!r}".format(device_name))

                # create a Device class instance for this device
                client_class = Device(client_socket, client_address, device_data, self.omniaController)
                self.omniaController.addDevice(client_class)
        
            # run main task for the new client, create resume event and wait for it
            if client_class:

                await self.runClient(client_mac, client_class)

            else:
                self.log.debug("Client not registered!")
                self.log.debug("Clients connected: {!r}".format( len(self.tasks) ))
                self.log.debug("----------------------")

    async def runClient(self, client_mac, client_class, client_socket=None):

        if client_socket:   # called from resume
            await client_class.resumeSocket(client_socket)  # pass to client the new socket
        else:
            client_task = await spawn(client_class.main)    # run main task
            self.tasks[client_mac] = {"task": client_task}  # add client's task to tasks

        ### close logging block ###
        self.log.debug("Clients connected: {!r}".format( len(self.tasks) ))
        self.log.debug("----------------------")
        ### --- ###

        event = Event()     # new resume event
        resume_event = await spawn(client_class.resumeEventListener, event)     # start event listener
        self.tasks[client_mac]["resume_event"] = event  # store resume event

        resume_client_class = await resume_event.join()    # wait for event listener to return client_class
        self.tasks[client_mac]["resume_class"] = resume_client_class   # set client_class, so that can be read when resuming