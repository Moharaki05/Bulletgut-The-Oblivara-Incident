import pygame as pg
from data.config import SCREEN_WIDTH, SCREEN_HEIGHT
from engine.audio_manager import AudioManager


class EndingScreen:
    def __init__(self):
        # Charger les polices
        self.font_large = pg.font.Font("assets/fonts/DooM.ttf", 45)
        self.font_medium = pg.font.Font("assets/fonts/DooM.ttf", 30)
        self.font_small = pg.font.Font("assets/fonts/DooM.ttf", 20)

        # Charger l'image de fond si elle existe
        try:
            self.background_image = pg.image.load("assets/ui/intermission_bg.png")
            self.background_image = pg.transform.scale(self.background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except FileNotFoundError:
            print("[WARNING] assets/ui/intermission_bg.png not found, using default background")
            self.background_image = None

        # Charger le texte depuis le fichier
        self.ending_text = self.load_ending_text()

        # Variables pour l'effet machine à écrire
        self.typewriter_speed = 0.05  # Secondes entre chaque caractère
        self.typewriter_timer = 0.0
        self.displayed_text = ""
        self.text_complete = False
        self.current_char_index = 0

        # Variables pour le texte clignotant "Press Enter"
        self.blink_timer = 0.0
        self.blink_interval = 0.8
        self.show_enter_text = True

        # État de l'écran
        self.active = False
        self.can_exit = False

        # Position du texte
        self.text_start_y = SCREEN_HEIGHT // 4
        self.line_spacing = 35
        self.text_margin_left = 100  # Marge gauche pour l'alignement

        # Gestionnaire audio pour la musique de fin
        self.audio_manager = AudioManager()
        self.music_started = False

        # Chemins des musiques possibles (par ordre de priorité)
        self.ending_music_path = "assets/music/ending.mp3"

    @staticmethod
    def load_ending_text():
        """Charge le texte de fin depuis un fichier"""
        try:
            with open("data/ending_text.txt", "r", encoding="utf-8") as file:
                return file.read().strip()
        except FileNotFoundError:
            print("[WARNING] data/ending_text.txt not found, using default text")
            # Message d'erreur - fichier texten non trouvé
            return """ending_text.txt is missing. Please provide the file in the data folder"""

    def start_ending_music(self):
        """Démarre la musique de fin"""
        if self.music_started:
            return

        music_path = self.ending_music_path
        if music_path:
            # Arrêter toute musique précédente
            self.audio_manager.stop_music()

            # Charger et jouer la musique de fin (boucle infinie)
            if self.audio_manager.load_and_play_music(music_path, loop=-1):
                self.music_started = True
                print(f"[ENDING] Started ending music: {music_path}")
            else:
                print(f"[ENDING] Failed to start ending music: {music_path}")
        else:
            print("[ENDING] No ending music available, continuing without music")
            self.music_started = True  # Éviter de réessayer

    def start(self):
        """Démarre l'écran de fin"""
        self.active = True
        self.displayed_text = ""
        self.text_complete = False
        self.current_char_index = 0
        self.can_exit = False
        self.typewriter_timer = 0.0
        self.blink_timer = 0.0
        self.show_enter_text = True
        self.music_started = False

        # Démarrer la musique de fin
        self.start_ending_music()

        print("[ENDING] Ending screen started")

    def update(self, dt):
        """Met à jour l'effet machine à écrire et les animations"""
        if not self.active:
            return

        # S'assurer que la musique joue si elle n'a pas démarré
        if not self.music_started:
            self.start_ending_music()

        # Effet machine à écrire
        if not self.text_complete:
            self.typewriter_timer += dt

            if self.typewriter_timer >= self.typewriter_speed:
                self.typewriter_timer = 0.0

                if self.current_char_index < len(self.ending_text):
                    self.displayed_text += self.ending_text[self.current_char_index]
                    self.current_char_index += 1
                else:
                    self.text_complete = True
                    self.can_exit = True
                    print("[ENDING] Text display complete, can now exit")

        # Animation du texte clignotant
        if self.text_complete:
            self.blink_timer += dt
            if self.blink_timer >= self.blink_interval:
                self.blink_timer = 0.0
                self.show_enter_text = not self.show_enter_text

    def render(self, screen):
        """Affiche l'écran de fin"""
        if not self.active:
            return

        # Fond
        if self.background_image:
            screen.blit(self.background_image, (0, 0))
        else:
            # Fond dégradé sombre
            screen.fill((10, 10, 15))
            for i in range(SCREEN_HEIGHT):
                color_value = int(10 + (i / SCREEN_HEIGHT) * 20)
                pg.draw.line(screen, (color_value, color_value, color_value + 5),
                             (0, i), (SCREEN_WIDTH, i))

        # Afficher le texte avec effet machine à écrire
        self.render_typewriter_text(screen)

        # Afficher le prompt "Press Enter" si le texte est complet
        if self.text_complete and self.show_enter_text:
            enter_text = "PRESS [ENTER] TO RETURN TO MAIN MENU"
            enter_surface = self.font_medium.render(enter_text, True, (255, 0, 0))
            enter_rect = enter_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
            screen.blit(enter_surface, enter_rect)

    def render_typewriter_text(self, screen):
        """Affiche le texte avec l'effet machine à écrire"""
        lines = self.displayed_text.split('\n')
        y_offset = self.text_start_y

        for line in lines:
            if line.strip():  # Si la ligne n'est pas vide
                # Vérifier si c'est un titre (première ligne en majuscules)
                if line == lines[0] and line.isupper():
                    text_surface = self.font_large.render(line, True, (255, 100, 100))
                    # Centrer seulement le titre
                    text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
                    screen.blit(text_surface, text_rect)
                    y_offset += self.line_spacing + 10  # Plus d'espace après le titre
                else:
                    text_surface = self.font_small.render(line, True, (255, 0, 0))
                    # Aligner le texte à gauche avec une marge
                    screen.blit(text_surface, (self.text_margin_left, y_offset))
                    y_offset += self.line_spacing
            else:
                # Ligne vide = saut de ligne
                y_offset += self.line_spacing // 2

    def handle_input(self, event):
        """Gère les entrées utilisateur"""
        if not self.active:
            return None

        if event.type == pg.KEYDOWN:
            if event.key == pg.K_RETURN and self.can_exit:
                # ⭐ NOUVEAU : Arrêter la musique avant de retourner au menu
                self.stop_music()
                return "return_to_menu"
            elif event.key == pg.K_SPACE and not self.text_complete:
                # Permettre de skip l'animation avec Espace
                self.displayed_text = self.ending_text
                self.text_complete = True
                self.can_exit = True
                self.current_char_index = len(self.ending_text)
                print("[ENDING] Text display skipped")

        return None

    def is_active(self):
        """Retourne True si l'écran de fin est actif"""
        return self.active

    def stop_music(self):
        """Arrête la musique de fin"""
        if self.music_started:
            self.audio_manager.stop_music()
            self.music_started = False
            print("[ENDING] Ending music stopped")

    def stop(self):
        """Arrête l'écran de fin"""
        self.active = False
        self.stop_music()
        print("[ENDING] Ending screen stopped")

    # ⭐ NOUVEAU : Méthodes pour contrôler la musique
    def pause_music(self):
        """Met en pause la musique de fin"""
        if self.music_started:
            self.audio_manager.pause_music()
            print("[ENDING] Ending music paused")

    def resume_music(self):
        """Reprend la musique de fin"""
        if self.music_started:
            self.audio_manager.resume_music()
            print("[ENDING] Ending music resumed")

    def set_music_volume(self, volume):
        """Définit le volume de la musique de fin (0.0 à 1.0)"""
        self.audio_manager.set_music_volume(volume)
        print(f"[ENDING] Ending music volume set to {volume}")

    def is_music_playing(self):
        """Vérifie si la musique de fin joue actuellement"""
        return self.music_started and self.audio_manager.is_playing()