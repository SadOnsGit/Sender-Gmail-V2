class BotConfig():
    def __init__(self, delay=2):
        self.delay = delay
        self.admins = [7428578184]
        self.count_messages = 300
        self.generation = False
    
    def update_delay(self, new_delay):
        self.delay = new_delay
        
    def get_delay(self):
        return self.delay
    
    def set_admin(self, id):
        self.admins.append(id)

    def get_admins(self):
        return self.admins
    
    def update_count_messages(self, count_messages):
        self.count_messages = count_messages
    
    def get_count_messages(self):
        return self.count_messages
    
    def get_generation(self):
        return self.generation
    
    def update_generation(self):
        if self.generation:
            self.generation = False
        else:
            self.generation = True


config = BotConfig()
