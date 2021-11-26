class User:
    username = ""
    passwd = ""
    uid = 0
    remember_token = ""
    server = "auto"

    def __init__(self, _username, _passwd, _uid, _remember_token, _server):
        self.username = _username
        self.passwd = _passwd
        self.uid = _uid
        self.remember_token = _remember_token
        self.server = _server
