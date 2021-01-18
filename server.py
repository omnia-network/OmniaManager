### Omnia libraries ###
from manager.omniaManager       import OmniaManager
### --- ###

users_path = "users/users.json"
devices_path = "devices/devices.json"
authorizations_path = "authorizations/authorizations.json"

# server IP address and port
ADDRESS = "192.168.1.10"
PORT = 50500                                # randomly chosen

omniaManager = OmniaManager(ADDRESS, PORT, users_path, devices_path, authorizations_path)

omniaManager.startManager()
