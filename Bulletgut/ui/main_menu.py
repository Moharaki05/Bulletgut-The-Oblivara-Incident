import pygame as pg
from data.config import SCREEN_WIDTH, SCREEN_HEIGHT
from engine.audio_manager import AudioManager


class MainMenu:
    def __init__(self):
        self.font_large = pg.font.Font("assets/fonts/DooM.ttf", 48)
        self.font_medium = pg.font.Font("assets/fonts/DooM.ttf", 32)
        self.font_small = pg.font.Font("assets/fonts/Born2bSportyFS.otf", 24)

        self.arrow_font_medium = pg.font.SysFont("Arial", 36)

        # Couleurs style Doom
        self.menu_text_color = (255, 0, 0)  # Rouge
        self.selected_color = (255, 255, 0)  # Jaune pour la sélection
        self.text_color = (255, 255, 255) # Blanc
        self.shadow_color = (64, 64, 64)  # Gris pour l'ombre
        self.audio_manager = AudioManager()

        # Options du menu
        self.menu_options = [
            "NEW GAME",
            "CREDITS",
            "HOW TO PLAY",
            "QUIT"
        ]

        self.selected_index = 0
        self.is_active = True

        # Modal de confirmation de sortie
        self.show_quit_modal = False
        self.quit_modal_options = ["YES", "NO"]
        self.quit_modal_selected = 1  # Sélectionner "NO" par défaut pour éviter les sorties accidentelles

        # Configuration de la musique du menu
        self.menu_music_path = "assets/music/title.mp3"  # Ou .mp3/.wav selon votre fichier
        self.music_loaded = False

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
            logo_width = min(600, SCREEN_WIDTH - 50)
            logo_height = int(self.logo.get_height() * (logo_width / self.logo.get_width()))
            self.logo = pg.transform.scale(self.logo, (logo_width / 1.25, logo_height / 1.25))
            print("[MAIN_MENU] Logo loaded successfully")
        except FileNotFoundError:
            # Si le logo n'existe pas, créer un texte de remplacement
            self.logo = None
            print("[WARNING] Logo not found at assets/ui/logo.png")

        # Positionnement à droite de l'écran
        self.menu_start_x = SCREEN_WIDTH - 450  # Position X des options (côté droit)
        self.menu_start_y = SCREEN_HEIGHT // 2 - 40  # Position Y de départ des options
        self.option_spacing = 65  # Espacement entre les options

        # Position du logo (côté droit aussi, au-dessus des options)
        if self.logo:
            self.logo_x = SCREEN_WIDTH - self.logo.get_width() - 50
            self.logo_y = self.menu_start_y - self.logo.get_height() + 50

    def load_menu_music(self):
        """Charge la musique du menu si elle n'est pas déjà chargée"""
        if not self.music_loaded:
            success = self.audio_manager.load_and_play_music(self.menu_music_path, loop=0)
            if success:
                self.music_loaded = True
                print("[MAIN_MENU] Menu music loaded and playing")
            else:
                print("[MAIN_MENU] Failed to load menu music - continuing without music")

    def show(self):
        """Affiche le menu principal"""
        self.is_active = True
        self.selected_index = 0
        self.show_quit_modal = False

        # Arrêter toute musique en cours et charger la musique du menu
        self.audio_manager.stop_music()
        self.music_loaded = False  # Reset pour recharger la musique
        self.load_menu_music()

    def hide(self):
        """Cache le menu principal"""
        self.is_active = False
        # Optionnel : arrêter la musique quand on quitte le menu
        # self.audio_manager.stop_music()

    def handle_input(self, event):
        """Gère les entrées clavier pour naviguer dans le menu"""
        if not self.is_active:
            return None

        if event.type == pg.KEYDOWN:
            # Si le modal de quit est affiché
            if self.show_quit_modal:
                if event.key == pg.K_LEFT or event.key == pg.K_a:
                    self.quit_modal_selected = (self.quit_modal_selected - 1) % len(self.quit_modal_options)
                    return "navigate_modal"
                elif event.key == pg.K_RIGHT or event.key == pg.K_d:
                    self.quit_modal_selected = (self.quit_modal_selected + 1) % len(self.quit_modal_options)
                    return "navigate_modal"
                elif event.key == pg.K_RETURN or event.key == pg.K_SPACE:
                    if self.quit_modal_selected == 0:  # YES
                        # Arrêter la musique avant de quitter
                        self.audio_manager.stop_music()
                        return "confirm_quit"
                    else:  # NO
                        self.show_quit_modal = False
                        return "cancel_quit"
                elif event.key == pg.K_ESCAPE:
                    self.show_quit_modal = False
                    return "cancel_quit"
            else:
                # Navigation normale du menu
                if event.key == pg.K_UP or event.key == pg.K_w:
                    self.selected_index = (self.selected_index - 1) % len(self.menu_options)
                    return "navigate"
                elif event.key == pg.K_DOWN or event.key == pg.K_s:
                    self.selected_index = (self.selected_index + 1) % len(self.menu_options)
                    return "navigate"
                elif event.key == pg.K_RETURN or event.key == pg.K_SPACE:
                    return self.get_selected_action()
                elif event.key == pg.K_ESCAPE:
                    # Afficher le modal de quit au lieu de quitter directement
                    self.show_quit_modal = True
                    self.quit_modal_selected = 1  # Sélectionner "NO" par défaut
                    return "show_quit_modal"
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
            # Afficher le modal de confirmation au lieu de quitter directement
            self.show_quit_modal = True
            self.quit_modal_selected = 1  # Sélectionner "NO" par défaut
            return "show_quit_modal"
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

    def render_quit_modal(self, screen):
        """Affiche le modal de confirmation de sortie"""
        # Créer une surface semi-transparente pour assombrir l'arrière-plan
        overlay = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)  # Transparence
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        # Dimensions et position du modal (plus large)
        modal_width = 1100
        modal_height = 250
        modal_x = (SCREEN_WIDTH - modal_width) // 2
        modal_y = (SCREEN_HEIGHT - modal_height) // 2

        # Dessiner le fond du modal avec bordure style Doom (inspiré du pause menu)
        # Bordure extérieure (relief)
        outer_rect = pg.Rect(modal_x - 10, modal_y - 10, modal_width + 20, modal_height + 20)
        pg.draw.rect(screen, (96, 96, 96), outer_rect)
        pg.draw.rect(screen, (160, 160, 160), outer_rect, 4)

        # Fond intérieur
        modal_rect = pg.Rect(modal_x, modal_y, modal_width, modal_height)
        pg.draw.rect(screen, (32, 32, 32), modal_rect)  # Même gris foncé que le pause menu

        # Titre du modal
        title_text = self.font_medium.render("YOU AIN'T CHICKENIN' OUT NOW, ARE YA?", True, (255, 0, 0))
        title_x = modal_x + (modal_width - title_text.get_width()) // 2
        title_y = modal_y + 40
        screen.blit(title_text, (title_x, title_y))

        # Options YES/NO avec plus d'espacement
        option_y = modal_y + 120
        option_spacing = 180  # Plus d'espace entre les options
        start_x = modal_x + (modal_width - (len(self.quit_modal_options) * option_spacing)) // 2

        for i, option in enumerate(self.quit_modal_options):
            color = self.selected_color if i == self.quit_modal_selected else self.text_color

            # Rendu du texte
            option_text = self.font_medium.render(option, True, color)
            option_x = start_x + i * option_spacing
            option_text_x = option_x + (option_spacing - option_text.get_width()) // 2

            screen.blit(option_text, (option_text_x, option_y))

            # Indicateur de sélection
            if i == self.quit_modal_selected:
                arrow = self.arrow_font_medium.render("►", True, self.selected_color)
                screen.blit(arrow, (option_text_x - 40, option_y))

        # Instructions du modal
        instruction_text = self.font_small.render("[←][→] Navigate • [ENTER] Confirm • [ESC] Cancel",
                                                  True, (255, 255, 255))
        instruction_x = modal_x + (modal_width - instruction_text.get_width()) // 2
        instruction_y = modal_y + modal_height - 50
        screen.blit(instruction_text, (instruction_x, instruction_y))

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
            color = self.selected_color if i == self.selected_index else self.menu_text_color

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
            if i == self.selected_index and not self.show_quit_modal:
                arrow = self.arrow_font_medium.render("►", True, self.selected_color)
                screen.blit(arrow, (text_x - 50, text_y))

        # Instructions en bas à droite
        if not self.show_quit_modal:
            instruction_text = self.font_small.render("[↑][↓] Navigate • [ENTER] Select • [ESC] Quit • [M] Music • [+/-] Volume",
                                                      True, (255, 255, 255))
            instruction_x = SCREEN_WIDTH - instruction_text.get_width() - 20
            instruction_y = SCREEN_HEIGHT - 40
            screen.blit(instruction_text, (instruction_x, instruction_y))

        # Version du jeu en bas à gauche (optionnel)
        version_text = self.font_small.render("by Mohamed Laraki - v 1.0", True, (255, 255, 255))
        screen.blit(version_text, (20, SCREEN_HEIGHT - 40))

        # Afficher le modal de quit si nécessaire
        if self.show_quit_modal:
            self.render_quit_modal(screen)