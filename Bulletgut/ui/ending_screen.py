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

        self.audio_manager = AudioManager()

    @staticmethod
    def load_ending_text():
        """Charge le texte de fin depuis un fichier"""
        try:
            with open("data/ending_text.txt", "r", encoding="utf-8") as file:
                return file.read().strip()
        except FileNotFoundError:
            print("[WARNING] data/ending_text.txt not found, using default text")
            # Texte par défaut (Lorem Ipsum thématique)
            return """ending_text.txt is missing. Please provide the file in the data folder"""

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
        self.audio_manager.stop_music()
        print("[ENDING] Ending screen started")

    def update(self, dt):
        """Met à jour l'effet machine à écrire et les animations"""
        if not self.active:
            return

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

    def stop(self):
        """Arrête l'écran de fin"""
        self.active = False
        print("[ENDING] Ending screen stopped")