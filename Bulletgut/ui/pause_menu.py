import pygame as pg
from data.config import SCREEN_WIDTH, SCREEN_HEIGHT


class PauseMenu:
    def __init__(self):
        self.font_large = pg.font.Font("assets/fonts/DooM.ttf", 48)
        self.font_medium = pg.font.Font("assets/fonts/DooM.ttf", 36)
        self.font_small = pg.font.Font("assets/fonts/DooM.ttf", 24)

        # Couleurs style Doom
        self.bg_color = (32, 32, 32)  # Gris foncé
        self.text_color = (255, 255, 255)  # Blanc
        self.selected_color = (255, 255, 0)  # Jaune pour la sélection
        self.shadow_color = (64, 64, 64)  # Gris pour l'ombre

        # Options du menu
        self.menu_options = [
            "RESUME GAME",
            "RESTART LEVEL",
            "QUIT GAME"
        ]

        self.selected_index = 0
        self.is_active = False

        # Charger le logo si disponible
        try:
            self.logo = pg.image.load("assets/ui/logo.png").convert_alpha()
            # Redimensionner le logo - plus grand maintenant
            logo_width = min(500, SCREEN_WIDTH - 50)  # Plus large
            logo_height = int(self.logo.get_height() * (logo_width / self.logo.get_width()))
            self.logo = pg.transform.scale(self.logo, (logo_width, logo_height))
        except:
            # Si le logo n'existe pas, créer un texte de remplacement
            self.logo = None
            print("[WARNING] Logo not found at assets/ui/logo.png")

        # Surface de fond semi-transparente
        self.overlay = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.overlay.set_alpha(128)
        self.overlay.fill((0, 0, 0))

        # Dimensions du menu principal - plus grand
        self.menu_width = 450
        self.menu_height = 320
        self.menu_x = (SCREEN_WIDTH - self.menu_width) // 2
        self.menu_y = (SCREEN_HEIGHT - self.menu_height) // 2

        # Ajuster la position si on a un logo
        if self.logo:
            self.logo_y = self.menu_y - self.logo.get_height() - 15  # Un peu moins d'espace
            if self.logo_y < 15:
                # Si pas assez de place en haut, décaler le menu vers le bas
                offset = 15 - self.logo_y
                self.logo_y = 15
                self.menu_y += offset

    def show(self):
        """Affiche le menu pause"""
        self.is_active = True
        self.selected_index = 0

    def hide(self):
        """Cache le menu pause"""
        self.is_active = False

    def handle_input(self, event):
        """Gère les entrées clavier pour naviguer dans le menu"""
        if not self.is_active:
            return None

        if event.type == pg.KEYDOWN:
            if event.key == pg.K_UP or event.key == pg.K_w:
                self.selected_index = (self.selected_index - 1) % len(self.menu_options)
                return "navigate"
            elif event.key == pg.K_DOWN or event.key == pg.K_s:
                self.selected_index = (self.selected_index + 1) % len(self.menu_options)
                return "navigate"
            elif event.key == pg.K_RETURN or event.key == pg.K_SPACE:
                return self.get_selected_action()
            elif event.key == pg.K_p:  # P pour fermer le menu aussi
                return "resume"

        return None

    def get_selected_action(self):
        """Retourne l'action correspondant à l'option sélectionnée"""
        if self.selected_index == 0:
            return "resume"
        elif self.selected_index == 1:
            return "restart"
        elif self.selected_index == 2:
            return "quit"
        return None

    def render(self, screen):
        """Affiche le menu pause"""
        if not self.is_active:
            return

        # Fond semi-transparent
        screen.blit(self.overlay, (0, 0))

        # Fond du menu principal avec bordure style Doom
        menu_rect = pg.Rect(self.menu_x - 10, self.menu_y - 10,
                            self.menu_width + 20, self.menu_height + 20)

        # Bordure extérieure (relief)
        pg.draw.rect(screen, (96, 96, 96), menu_rect)
        pg.draw.rect(screen, (160, 160, 160), menu_rect, 4)

        # Fond intérieur
        inner_rect = pg.Rect(self.menu_x, self.menu_y, self.menu_width, self.menu_height)
        pg.draw.rect(screen, self.bg_color, inner_rect)

        # Afficher le logo
        if self.logo:
            logo_x = (SCREEN_WIDTH - self.logo.get_width()) // 2
            screen.blit(self.logo, (logo_x, self.logo_y))
        else:
            # Texte de titre si pas de logo
            title_text = self.font_large.render("BULLETGUT", True, self.text_color)
            title_x = (SCREEN_WIDTH - title_text.get_width()) // 2
            title_y = self.menu_y - 60
            screen.blit(title_text, (title_x, title_y))

        # Afficher les options du menu
        option_start_y = self.menu_y + 50
        option_spacing = 60

        for i, option in enumerate(self.menu_options):
            # Couleur selon si l'option est sélectionnée
            color = self.selected_color if i == self.selected_index else self.text_color

            # Rendu du texte avec ombre
            shadow_text = self.font_medium.render(option, True, self.shadow_color)
            main_text = self.font_medium.render(option, True, color)

            text_x = (SCREEN_WIDTH - main_text.get_width()) // 2
            text_y = option_start_y + i * option_spacing

            # Ombre
            screen.blit(shadow_text, (text_x + 2, text_y + 2))
            # Texte principal
            screen.blit(main_text, (text_x, text_y))

            # Indicateur de sélection (flèche ou bordure)
            if i == self.selected_index:
                # Flèches de chaque côté
                arrow_left = self.font_medium.render("►", True, self.selected_color)
                arrow_right = self.font_medium.render("◄", True, self.selected_color)

                screen.blit(arrow_left, (text_x - 40, text_y))
                screen.blit(arrow_right, (text_x + main_text.get_width() + 20, text_y))

        # Instructions en bas
        instruction_text = self.font_small.render("↑↓ Navigate • ENTER Select • P Resume",
                                                  True, (128, 128, 128))
        instruction_x = (SCREEN_WIDTH - instruction_text.get_width()) // 2
        instruction_y = self.menu_y + self.menu_height - 30
        screen.blit(instruction_text, (instruction_x, instruction_y))