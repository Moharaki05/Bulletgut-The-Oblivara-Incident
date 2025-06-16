import pygame as pg
from data.config import SCREEN_WIDTH, SCREEN_HEIGHT

class CreditsScreen:
    def __init__(self):
        self.font_large = pg.font.Font("assets/fonts/DooM.ttf", 48)
        self.font_medium = pg.font.Font("assets/fonts/DooM.ttf", 32)
        self.font_small = pg.font.Font("assets/fonts/Born2bSportyFS.otf", 24)

        # Couleurs
        self.bg_color = (16, 16, 16)  # Noir très foncé
        self.title_color = (255, 255, 255)
        self.text_color = (200, 200, 200)
        self.section_color = (255, 0, 0)  # Jaune pour les noms/rôles
        self.highlight_color = (255, 255, 0)  # Jaune pour les noms/rôles
        self.shadow_color = (64, 64, 64)

        self.is_active = False

        # Animation de défilement
        self.scroll_y = SCREEN_HEIGHT
        self.scroll_speed = 30  # pixels par seconde
        self.content_height = 0  # Calculé dynamiquement

        # Contenu des crédits
        self.credits_content = [
            ("BULLETGUT:", "title"),
            ("THE OBLIVARA INCIDENT", "title"),
            ("", "space"),
            ("DEVELOPMENT TEAM", "section"),
            ("", "space_small"),
            ("Game Design & Programming", "role"),
            ("Mohamed LARAKI", "name"),
            ("Claude AI", "name"),
            ("ChatGPT", "name"),
            ("", "space_small"),
            ("Level Design", "role"),
            ("Mohamed Laraki", "name"),
            ("", "space_small"),
            ("Art & Graphics", "role"),
            ("Freedoom Community", "name"),
            ("Little Martian", "name"),
            ("Open Game Art", "name"),
            ("", "space_small"),
            ("Sound & Music", "role"),
            ("Music : PDKMusic", "name"),
            ("Sounds : Freesound", "name"),
            ("Sounds : Pixabay", "name"),
            ("Sounds : Bobby Prince", "name"),
            ("", "space"),
            ("SPECIAL THANKS", "section"),
            ("", "space_small"),
            ("Daniel Lemire", "name"),
            ("", "space"),
            ("TOOLS & LIBRARIES", "section"),
            ("", "space_small"),
            ("Python 3.x", "name"),
            ("Pygame", "name"),
            ("Tiled Map Editor", "name"),
            ("", "space"),
            # ("ASSETS", "section"),
            # ("", "space_small"),
            # ("Font: DooM.ttf", "name"),
            # ("Font: Born2bSportyFS.otf", "name"),
            # ("Various texture sources", "name"),
            # ("", "space"),
            # ("", "space"),
            ("Thank you for playing!", "thank_you"),
            ("", "space"),
            ("Visit us at: https://github.com/Moharaki05/Bulletgut-The-Oblivara-Incident", "website"),
            ("", "space"),
            ("", "space"),
            ("Press [ESC] to return to menu", "instruction")
        ]

        # Calculer la hauteur totale du contenu
        self.calculate_content_height()

    def calculate_content_height(self):
        """Calcule la hauteur totale du contenu pour l'animation"""
        height = 0
        for text, text_type in self.credits_content:
            if text_type == "title":
                height += 60
            elif text_type == "section":
                height += 50
            elif text_type == "role":
                height += 40
            elif text_type == "name":
                height += 35
            elif text_type == "thank_you":
                height += 50
            elif text_type == "website":
                height += 35
            elif text_type == "instruction":
                height += 40
            elif text_type == "space":
                height += 40
            elif text_type == "space_small":
                height += 20

        self.content_height = height

    def show(self):
        """Affiche l'écran des crédits"""
        self.is_active = True
        # Réinitialiser le défilement
        self.scroll_y = SCREEN_HEIGHT

    def hide(self):
        """Cache l'écran des crédits"""
        self.is_active = False

    def update(self, dt):
        """Met à jour l'animation de défilement"""
        if not self.is_active:
            return

        # Faire défiler vers le haut
        self.scroll_y -= self.scroll_speed * dt

        # Recommencer le défilement si on a atteint la fin
        if self.scroll_y < -self.content_height:
            self.scroll_y = SCREEN_HEIGHT

    def handle_input(self, event):
        """Gère les entrées pour revenir au menu"""
        if not self.is_active:
            return None

        if event.type == pg.KEYDOWN:
            if (event.key == pg.K_ESCAPE or
                    event.key == pg.K_RETURN or
                    event.key == pg.K_SPACE):
                return "back_to_menu"

        return None

    def render(self, screen):
        """Affiche l'écran des crédits avec défilement"""
        if not self.is_active:
            return

        # Fond
        screen.fill(self.bg_color)

        # Rendu du contenu avec défilement
        current_y = self.scroll_y

        for text, text_type in self.credits_content:
            if text.strip():  # Ignorer les lignes vides
                # Choisir la police et la couleur selon le type
                if text_type == "title":
                    font = self.font_large
                    color = self.title_color
                    # Centrer le titre
                    text_surface = font.render(text, True, color)
                    shadow_surface = font.render(text, True, self.shadow_color)
                    x = (SCREEN_WIDTH - text_surface.get_width()) // 2

                    # Ne dessiner que si visible à l'écran
                    if -60 <= current_y <= SCREEN_HEIGHT:
                        screen.blit(shadow_surface, (x + 3, current_y + 3))
                        screen.blit(text_surface, (x, current_y))

                elif text_type == "section":
                    font = self.font_medium
                    color = self.section_color
                    text_surface = font.render(text, True, color)
                    x = (SCREEN_WIDTH - text_surface.get_width()) // 2

                    if -50 <= current_y <= SCREEN_HEIGHT:
                        screen.blit(text_surface, (x, current_y))

                elif text_type == "role":
                    font = self.font_small
                    color = self.highlight_color
                    text_surface = font.render(text, True, color)
                    x = (SCREEN_WIDTH - text_surface.get_width()) // 2

                    if -40 <= current_y <= SCREEN_HEIGHT:
                        screen.blit(text_surface, (x, current_y))

                elif text_type == "name":
                    font = self.font_small
                    color = self.text_color
                    text_surface = font.render(text, True, color)
                    x = (SCREEN_WIDTH - text_surface.get_width()) // 2

                    if -35 <= current_y <= SCREEN_HEIGHT:
                        screen.blit(text_surface, (x, current_y))

                elif text_type == "thank_you":
                    font = self.font_medium
                    color = self.title_color
                    text_surface = font.render(text, True, color)
                    shadow_surface = font.render(text, True, self.shadow_color)
                    x = (SCREEN_WIDTH - text_surface.get_width()) // 2

                    if -50 <= current_y <= SCREEN_HEIGHT:
                        screen.blit(shadow_surface, (x + 2, current_y + 2))
                        screen.blit(text_surface, (x, current_y))

                elif text_type == "website":
                    font = self.font_small
                    color = (100, 150, 255)  # Bleu pour les liens
                    text_surface = font.render(text, True, color)
                    x = (SCREEN_WIDTH - text_surface.get_width()) // 2

                    if -35 <= current_y <= SCREEN_HEIGHT:
                        screen.blit(text_surface, (x, current_y))

                elif text_type == "instruction":
                    font = self.font_small
                    color = (128, 128, 128)
                    text_surface = font.render(text, True, color)
                    x = (SCREEN_WIDTH - text_surface.get_width()) // 2

                    if -40 <= current_y <= SCREEN_HEIGHT:
                        screen.blit(text_surface, (x, current_y))

            # Avancer à la prochaine ligne selon le type
            if text_type == "title":
                current_y += 60
            elif text_type == "section":
                current_y += 50
            elif text_type == "role":
                current_y += 40
            elif text_type == "name":
                current_y += 35
            elif text_type == "thank_you":
                current_y += 50
            elif text_type == "website":
                current_y += 35
            elif text_type == "instruction":
                current_y += 40
            elif text_type == "space":
                current_y += 40
            elif text_type == "space_small":
                current_y += 20