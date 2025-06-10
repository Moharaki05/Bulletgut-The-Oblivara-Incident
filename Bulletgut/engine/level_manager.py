class LevelManager:
    def __init__(self, level_paths):
        self.level_paths = level_paths
        self.index = 0

    def get_current(self):
        return self.level_paths[self.index]

    def get_next(self):
        if self.index + 1 < len(self.level_paths):
            return self.level_paths[self.index + 1]
        return None

    def advance(self):
        if self.index + 1 < len(self.level_paths):
            self.index += 1
            return self.level_paths[self.index]
        return None

    def restart(self):
        return self.level_paths[self.index]
