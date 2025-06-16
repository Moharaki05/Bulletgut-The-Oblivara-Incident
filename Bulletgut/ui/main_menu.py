import pygame as pg
from data.config import SCREEN_WIDTH, SCREEN_HEIGHT


class MainMenu:
    def __init__(self):
        self.font_large = pg.font.Font("assets/fonts/DooM.ttf", 48)
        self.font_medium = pg.font.Font("assets/fonts/DooM.ttf", 36)
        self.font_small = pg.font.Font("assets/fonts/Born2bSportyFS.otf", 24)

        self.arrow_font_medium = pg.font.SysFont("Arial", 36)

        # Couleurs style Doom
        self.text_color = (255, 255, 255)  # Blanc
        self.selected_color = (255, 0, 0)  # Rouge pour la sélection
        self.shadow_color = (64, 64, 64)  # Gris pour l'ombre

        # Options du menu
        self.menu_options = [
            "NEW GAME",
            "CREDITS",
            "HOW TO PLAY",
            "QUIT"
        ]

        self.selected_index = 0
        self.is_active = True

        # Charger le fond personnalisé
        try:
            self.background = pg.image.load("assets/ui/main_menu_bg.png").convert()
            # Redimensionner le fond pour qu'il remplisse l'écran
            self.background = pg.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
            print("[MAIN_MENU] Background loaded successfully")
        except FileNotFoundError:
            # Si le fond n'existe pas, créer un fond dégradé sombre
            self.background = None
            print("[WARNING] Background not found at assets/ui/main_menu_bg.png - using fallback")

        # Charger le logo
        try:
            self.logo = pg.image.load("assets/ui/logo.png").convert_alpha()
            # Redimensionner le logo pour qu'il soit plus grand
            logo_width = min(600, SCREEN_WIDTH - 100)
            logo_height = int(self.logo.get_height() * (logo_width / self.logo.get_width()))
            self.logo = pg.transform.scale(self.logo, (logo_width, logo_height))
            print("[MAIN_MENU] Logo loaded successfully")
        except FileNotFoundError:
            # Si le logo n'existe pas, créer un texte de remplacement
            self.logo = None
            print("[WARNING] Logo not found at assets/ui/logo.png")

        # Positionnement à droite de l'écran
        self.menu_start_x = SCREEN_WIDTH - 400  # Position X des options (côté droit)
        self.menu_start_y = SCREEN_HEIGHT // 2 + 50  # Position Y de départ des options
        self.option_spacing = 80  # Espacement entre les options

        # Position du logo (côté droit aussi, au-dessus des options)
        if self.logo:
            self.logo_x = SCREEN_WIDTH - self.logo.get_width() - 50
            self.logo_y = self.menu_start_y - self.logo.get_height() - 80

    def show(self):
        """Affiche le menu principal"""
        self.is_active = True
        self.selected_index = 0

    def hide(self):
        """Cache le menu principal"""
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
            elif event.key == pg.K_ESCAPE:
                return "quit"

        return None

    def get_selected_action(self):
        """Retourne l'action correspondant à l'option sélectionnée"""
        if self.selected_index == 0:
            return "new_game"
        elif self.selected_index == 1:
            return "credits"
        elif self.selected_index == 2:
            return "how_to_play"
        elif self.selected_index == 3:
            return "quit"
        return None

    @staticmethod
    def create_fallback_background(screen):
        """Crée un fond dégradé sombre si l'image de fond n'est pas disponible"""
        # Créer un dégradé vertical du noir vers le gris foncé
        for y in range(SCREEN_HEIGHT):
            # Calculer l'intensité du gris en fonction de la position Y
            intensity = int(32 * (y / SCREEN_HEIGHT))  # De 0 à 32
            color = (intensity, intensity, intensity)
            pg.draw.line(screen, color, (0, y), (SCREEN_WIDTH, y))

    def render(self, screen):
        """Affiche le menu principal"""
        if not self.is_active:
            return

        # Afficher le fond
        if self.background:
            screen.blit(self.background, (0, 0))
        else:
            # Fond de secours
            self.create_fallback_background(screen)

        # Afficher le logo
        if self.logo:
            screen.blit(self.logo, (self.logo_x, self.logo_y))
        else:
            # Texte de titre si pas de logo - aligné à droite aussi
            title_text = self.font_large.render("BULLETGUT", True, self.text_color)
            title_x = self.menu_start_x
            title_y = self.menu_start_y - 120
            # Ombre pour le titre
            shadow_title = self.font_large.render("BULLETGUT", True, self.shadow_color)
            screen.blit(shadow_title, (title_x + 3, title_y + 3))
            screen.blit(title_text, (title_x, title_y))

        # Afficher les options du menu (alignées à gauche)
        for i, option in enumerate(self.menu_options):
            # Couleur selon si l'option est sélectionnée
            color = self.selected_color if i == self.selected_index else self.text_color

            # Rendu du texte avec ombre
            shadow_text = self.font_medium.render(option, True, self.shadow_color)
            main_text = self.font_medium.render(option, True, color)

            # Position alignée à gauche (pas centrée)
            text_x = self.menu_start_x
            text_y = self.menu_start_y + i * self.option_spacing

            # Ombre
            screen.blit(shadow_text, (text_x + 2, text_y + 2))
            # Texte principal
            screen.blit(main_text, (text_x, text_y))

            # Indicateur de sélection (flèche à gauche de l'option sélectionnée)
            if i == self.selected_index:
                arrow = self.arrow_font_medium.render("►", True, self.selected_color)
                screen.blit(arrow, (text_x - 50, text_y))

        # Instructions en bas à droite
        instruction_text = self.font_small.render("[↑][↓] Navigate • [ENTER] Select • [ESC] Quit",
                                                  True, (128, 128, 128))
        instruction_x = SCREEN_WIDTH - instruction_text.get_width() - 20
        instruction_y = SCREEN_HEIGHT - 40
        screen.blit(instruction_text, (instruction_x, instruction_y))

        # Version du jeu en bas à gauche (optionnel)
        version_text = self.font_small.render("BULLETGUT v1.0 - The Oblivara Incident", True, (96, 96, 96))
        screen.blit(version_text, (20, SCREEN_HEIGHT - 40))