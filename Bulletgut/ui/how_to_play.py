import pygame as pg
from data.config import SCREEN_WIDTH, SCREEN_HEIGHT


class HowToPlayScreen:
    def __init__(self):
        self.font_large = pg.font.Font("assets/fonts/DooM.ttf", 48)
        self.font_medium = pg.font.Font("assets/fonts/DooM.ttf", 32)
        self.font_small = pg.font.Font("assets/fonts/Born2bSportyFS.otf", 24)

        # Couleurs
        self.bg_color = (16, 16, 16)  # Noir très foncé
        self.title_color = (255, 255, 255)
        self.text_color = (200, 200, 200)
        self.highlight_color = (255, 255, 0)  # Jaune pour les touches
        self.shadow_color = (64, 64, 64)

        self.is_active = False

        # Contenu des instructions
        self.instructions = [
            ("MOVEMENT", [
                "W, A, S, D - Move around",
                "Mouse - Look around"
            ]),
            ("COMBAT", [
                "Left Click - Fire weapon",
                "Mouse Wheel - Switch weapons",
            ]),
            ("INTERACTION", [
                "E - Open doors / Interact",
                "ESC - Pause menu"
            ]),
            ("OBJECTIVE", [
                "Find the exit to complete the level",
                "Collect items and eliminate enemies",
                "Survive at all costs!"
            ])
        ]

    def show(self):
        """Affiche l'écran How to Play"""
        self.is_active = True

    def hide(self):
        """Cache l'écran How to Play"""
        self.is_active = False

    def handle_input(self, event):
        """Gère les entrées pour revenir au menu"""
        if not self.is_active:
            return None

        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE or event.key == pg.K_RETURN or event.key == pg.K_SPACE:
                return "back_to_menu"

        return None

    def render(self, screen):
        """Affiche l'écran How to Play"""
        if not self.is_active:
            return

        # Fond
        screen.fill(self.bg_color)

        # Titre principal avec ombre
        title_text = self.font_large.render("HOW TO PLAY", True, self.title_color)
        title_shadow = self.font_large.render("HOW TO PLAY", True, self.shadow_color)
        title_x = (SCREEN_WIDTH - title_text.get_width()) // 2
        title_y = 50

        screen.blit(title_shadow, (title_x + 3, title_y + 3))
        screen.blit(title_text, (title_x, title_y))

        # Afficher les sections d'instructions
        current_y = 150
        section_spacing = 120
        line_spacing = 35

        for section_title, section_lines in self.instructions:
            # Titre de section
            section_text = self.font_medium.render(section_title, True, self.highlight_color)
            section_x = 100
            screen.blit(section_text, (section_x, current_y))
            current_y += 50

            # Lignes de la section
            for line in section_lines:
                # Séparer les touches/actions du texte pour les mettre en surbrillance
                if " - " in line:
                    key_part, desc_part = line.split(" - ", 1)

                    # Rendu de la partie touche en surbrillance
                    key_text = self.font_small.render(key_part, True, self.highlight_color)
                    screen.blit(key_text, (section_x + 20, current_y))

                    # Rendu du séparateur
                    sep_text = self.font_small.render(" - ", True, self.text_color)
                    screen.blit(sep_text, (section_x + 20 + key_text.get_width(), current_y))

                    # Rendu de la description
                    desc_text = self.font_small.render(desc_part, True, self.text_color)
                    screen.blit(desc_text, (section_x + 20 + key_text.get_width() + sep_text.get_width(), current_y))
                else:
                    # Ligne simple sans formatage spécial
                    line_text = self.font_small.render(line, True, self.text_color)
                    screen.blit(line_text, (section_x + 20, current_y))

                current_y += line_spacing

            current_y += section_spacing - len(section_lines) * line_spacing

        # Instructions de retour en bas
        back_text = self.font_small.render("Press [ESC], [ENTER] or [SPACE] to return to menu",
                                           True, (128, 128, 128))
        back_x = (SCREEN_WIDTH - back_text.get_width()) // 2
        back_y = SCREEN_HEIGHT - 60
        screen.blit(back_text, (back_x, back_y))