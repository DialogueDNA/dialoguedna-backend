from app.client.client import Client

class ClientsManager:
    def __init__(self):
        self.clients = {}

    def get_client(self, client_name: str) -> Client:
        if client_name not in self.clients:
            self.clients[client_name] = Client(client_name)
        return self.clients[client_name]
