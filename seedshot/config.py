import yaml

SECRETS = ["imgur-client-id", "twitch-oauth-token"]

class Config:
    def __init__(self, file_name="config.yaml", credentials_file_name="credentials.yaml"):
        self.file_name = file_name
        with open(self.file_name) as f:
            self._config = yaml.load(f, Loader=yaml.Loader)

        haveAllSecrets = True
        for secret in SECRETS:
            if not secret in self._config:
                haveAllSecrets = False

        if not haveAllSecrets:
            with open(credentials_file_name) as f:
                secrets_yaml = yaml.load(f, Loader=yaml.Loader)
                for secret in SECRETS:
                    if not secret in self._config:
                        self._config[secret] = secrets_yaml[secret]

    def __getitem__(self, key):
        return self._config[key]

    def safe_secret(_, secret):
        return secret[:2] + (len(secret)-2) * "*"

    def safe_to_str(self):
        config = self._config.copy()
        for secret in SECRETS:
            config[secret] = self.safe_secret(config[secret])

        return f"{config}"
