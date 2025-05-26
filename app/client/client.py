import os

class Client:
    def __init__(self, client_name: str, base_dir: str = "clients_data"):
        self.name = client_name
        self.base_path = os.path.join(base_dir, client_name)
        os.makedirs(self.base_path, exist_ok=True)

    def get_base_path(self) -> str:
        return self.base_path

    def get_client_name(self) -> str:
        return self.name

