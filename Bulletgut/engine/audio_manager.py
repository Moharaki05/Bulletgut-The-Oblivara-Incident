import pygame as pg
import os

class AudioManager:
    def __init__(self):
        self.current_music = None
        self.music_volume = 0.7
        self.is_music_playing = False

        # Initialiser le mixer audio si pas déjà fait
        if not pg.mixer.get_init():
            pg.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

    def load_and_play_music(self, music_path, loop=-1):
        """
        Charge et joue une musique
        loop=-1 pour boucle infinie, 0 pour une seule fois
        """
        if not music_path or not os.path.exists(music_path):
            print(f"[WARNING] Music file not found: {music_path}")
            return False

        try:
            # Arrêter la musique actuelle si elle joue
            if self.is_music_playing:
                pg.mixer.music.stop()

            # Charger et jouer la nouvelle musique
            pg.mixer.music.load(music_path)
            pg.mixer.music.set_volume(self.music_volume)
            pg.mixer.music.play(loop)

            self.current_music = music_path
            self.is_music_playing = True

            print(f"[DEBUG] Playing music: {os.path.basename(music_path)}")
            return True

        except pg.error as e:
            print(f"[ERROR] Failed to load music {music_path}: {e}")
            return False

    def stop_music(self):
        """Arrête la musique actuelle"""
        if self.is_music_playing:
            pg.mixer.music.stop()
            self.is_music_playing = False
            self.current_music = None
            print("[DEBUG] Music stopped")

    def pause_music(self):
        """Met en pause la musique"""
        if self.is_music_playing:
            pg.mixer.music.pause()
            print("[DEBUG] Music paused")

    def resume_music(self):
        """Reprend la musique"""
        if self.current_music:
            pg.mixer.music.unpause()
            print("[DEBUG] Music resumed")

    def set_music_volume(self, volume):
        """Définit le volume de la musique (0.0 à 1.0)"""
        self.music_volume = max(0.0, min(1.0, volume))
        pg.mixer.music.set_volume(self.music_volume)
        print(f"[DEBUG] Music volume set to {self.music_volume}")

    def is_playing(self):
        """Vérifie si la musique joue actuellement"""
        return pg.mixer.music.get_busy() and self.is_music_playing

    def get_current_music(self):
        """Retourne le chemin de la musique actuelle"""
        return self.current_music
