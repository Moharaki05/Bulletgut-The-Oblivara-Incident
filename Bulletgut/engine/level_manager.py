class LevelManager:
    def __init__(self, level_paths):
        self.level_paths = level_paths
        self.index = 0
        self.max_reached_level = 0  # Niveau le plus élevé atteint

    def get_current(self):
        return self.level_paths[self.index]

    def get_next(self):
        if self.index + 1 < len(self.level_paths):
            return self.level_paths[self.index + 1]
        return None

    def advance(self):
        if self.index + 1 < len(self.level_paths):
            self.index += 1
            # Mettre à jour le niveau le plus élevé atteint
            if self.index > self.max_reached_level:
                self.max_reached_level = self.index
            print(f"[DEBUG] Advanced to level {self.index + 1}/{len(self.level_paths)}")
            return self.level_paths[self.index]
        print("[DEBUG] No more levels available - game should end")
        return None

    def restart(self):
        """Redémarre le niveau actuel"""
        print(f"[DEBUG] Restarting level {self.index + 1}")
        return self.level_paths[self.index]

    def restart_from_beginning(self):
        """Redémarre depuis le premier niveau (utilisé lors de la mort)"""
        self.index = 0
        print("[DEBUG] Restarting from beginning due to death")
        return self.level_paths[self.index]

    def get_current_level_number(self):
        """Retourne le numéro du niveau actuel (1-indexé)"""
        return self.index + 1

    def get_total_levels(self):
        """Retourne le nombre total de niveaux"""
        return len(self.level_paths)

    def is_last_level(self):
        """Vérifie si c'est le dernier niveau"""
        return self.index >= len(self.level_paths) - 1

    def get_progress_percentage(self):
        """Retourne le pourcentage de progression"""
        return (self.index / len(self.level_paths)) * 100 if self.level_paths else 0

    def has_next_level(self):
        """Vérifie s'il y a un niveau suivant"""
        return self.index + 1 < len(self.level_paths)