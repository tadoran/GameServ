class Spectator:
    def __init__(self):
        self.history = ""

    def print(self, new_txt, *args, **kwargs):
        self.history += str(new_txt)
        print(new_txt, *args, **kwargs)
