from joiclient import JoiClient
import enviro

device_id = enviro.get_value("device_id")
client = JoiClient(device_id)
resident = client.get_Resident()
print(resident)

