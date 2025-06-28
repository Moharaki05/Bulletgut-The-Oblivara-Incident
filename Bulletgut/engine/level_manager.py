from engine.audio_manager import AudioManager


class LevelManager:
    def __init__(self, level_paths):
        self.level_paths = level_paths
        self.index = 0
        self.max_reached_level = 0  # Niveau le plus élevé atteint
        self.audio_manager = AudioManager()  # Gestionnaire audio
        self.current_level_music = None  # Track de la musique actuelle

    def get_current(self):
        """Retourne le chemin du niveau actuel"""
        return self.level_paths[self.index]

    def get_current_path(self):
        """Alias pour get_current() pour plus de clarté"""
        return self.level_paths[self.index]

    def get_next(self):
        if self.index + 1 < len(self.level_paths):
            return self.level_paths[self.index + 1]
        return None

    def advance(self):
        """Avance au niveau suivant (version originale sans musique)"""
        if self.index + 1 < len(self.level_paths):
            self.index += 1
            # Mettre à jour le niveau le plus élevé atteint
            if self.index > self.max_reached_level:
                self.max_reached_level = self.index
            print(f"[DEBUG] Advanced to level {self.index + 1}/{len(self.level_paths)}")
            return self.level_paths[self.index]
        print("[DEBUG] No more levels available - game should end")
        return None

    def advance_with_music(self, new_level_object):
        """Avance au niveau suivant avec gestion de la musique"""
        if self.index + 1 < len(self.level_paths):
            self.index += 1
            if self.index > self.max_reached_level:
                self.max_reached_level = self.index

            # Charger la musique du nouveau niveau
            self.load_level_music(new_level_object)

            print(f"[DEBUG] Advanced to level {self.index + 1}/{len(self.level_paths)}")
            return self.level_paths[self.index]

        print("[DEBUG] No more levels available - game should end")
        return None

    def load_level_music(self, level_object):
        """Charge la musique d'un objet Level"""
        if hasattr(level_object, 'music_file') and level_object.music_file:
            # Ne recharger que si c'est une musique différente
            if level_object.music_file != self.current_level_music:
                success = self.audio_manager.load_and_play_music(level_object.music_file)
                if success:
                    self.current_level_music = level_object.music_file
                    print(f"[DEBUG] Loaded music: {level_object.music_file}")
                else:
                    print(f"[WARNING] Failed to load music: {level_object.music_file}")
            else:
                print(f"[DEBUG] Same music already playing: {level_object.music_file}")
        else:
            # Pas de musique spécifiée, arrêter la musique actuelle
            if self.current_level_music:
                print("[DEBUG] No music specified, stopping current music")
                self.audio_manager.stop_music()
                self.current_level_music = None

    def restart(self):
        """Redémarre le niveau actuel"""
        print(f"[DEBUG] Restarting level {self.index + 1}")
        return self.level_paths[self.index]

    def restart_with_music(self, level_object):
        """Redémarre le niveau avec sa musique"""
        print(f"[DEBUG] Restarting level {self.index + 1}")
        self.load_level_music(level_object)
        return self.level_paths[self.index]

    def restart_from_beginning(self):
        """Redémarre depuis le premier niveau (utilisé lors de la mort)"""
        self.index = 0
        print("[DEBUG] Restarting from beginning due to death")
        return self.level_paths[self.index]

    def restart_from_beginning_with_music(self, first_level_object):
        """Redémarre depuis le premier niveau avec sa musique"""
        self.index = 0
        self.load_level_music(first_level_object)
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

    # Méthodes pour contrôler la musique
    def pause_music(self):
        """Met en pause la musique du niveau"""
        self.audio_manager.pause_music()

    def resume_music(self):
        """Reprend la musique du niveau"""
        self.audio_manager.resume_music()

    def set_music_volume(self, volume):
        """Définit le volume de la musique (0.0 à 1.0)"""
        self.audio_manager.set_music_volume(volume)

    def stop_music(self):
        """Arrête complètement la musique"""
        self.audio_manager.stop_music()
        self.current_level_music = None

    def get_current_music(self):
        """Retourne le chemin de la musique actuellement jouée"""
        return self.current_level_music

    def is_music_playing(self):
        """Vérifie si de la musique joue actuellement"""
        return self.audio_manager.is_playing()