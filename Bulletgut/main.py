import pygame as pg
from engine.game import Game
from ui.main_menu import MainMenu
from ui.credits import CreditsScreen
from ui.how_to_play import HowToPlayScreen
from data.config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS


class GameManager:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pg.display.set_caption("Bulletgut: The Oblivara Incident")

        # Charger et définir l'icône personnalisée
        try:
            icon = pg.image.load("assets/ui/icon.png")
            pg.display.set_icon(icon)
            print("[GAME_MANAGER] Custom icon loaded successfully")
        except Exception as e:
            print(f"[GAME_MANAGER] Could not load custom icon: {e}")
            print("[GAME_MANAGER] Using default pygame icon")

        self.clock = pg.time.Clock()
        self.running = True

        # États du jeu
        self.state = "main_menu"  # "main_menu", "game", "credits", "how_to_play"

        # Initialiser les écrans
        self.main_menu = MainMenu()
        self.credits_screen = CreditsScreen()
        self.how_to_play_screen = HowToPlayScreen()
        self.game = None

        # Contrôle de la souris pour les menus
        pg.event.set_grab(False)
        pg.mouse.set_visible(True)

    def start_game(self):
        """Démarre une nouvelle partie"""
        try:
            # Activer le contrôle souris pour le jeu
            pg.event.set_grab(True)
            pg.mouse.set_visible(False)

            self.game = Game()
            self.state = "game"
            print("[GAME_MANAGER] New game started")
        except Exception as e:
            print(f"[GAME_MANAGER] Error starting game: {e}")
            # Retourner au menu en cas d'erreur
            self.return_to_menu()

    def return_to_menu(self):
        """Retourne au menu principal"""
        # Désactiver le contrôle souris
        pg.event.set_grab(False)
        pg.mouse.set_visible(True)

        # Nettoyer le jeu si nécessaire
        if self.game:
            self.game = None

        self.state = "main_menu"
        self.main_menu.show()
        print("[GAME_MANAGER] Returned to main menu")

    def show_credits(self):
        """Affiche l'écran des crédits"""
        self.state = "credits"
        self.credits_screen.show()

    def show_how_to_play(self):
        """Affiche l'écran How to Play"""
        self.state = "how_to_play"
        self.how_to_play_screen.show()

    def handle_events(self):
        """Gère les événements selon l'état actuel"""
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
                return

            # Gestion selon l'état
            if self.state == "main_menu":
                action = self.main_menu.handle_input(event)
                if action == "new_game":
                    self.start_game()
                elif action == "credits":
                    self.show_credits()
                elif action == "how_to_play":
                    self.show_how_to_play()
                elif action == "confirm_quit":
                    # L'utilisateur a confirmé qu'il veut quitter
                    self.running = False
                elif action in ["show_quit_modal", "cancel_quit", "navigate_modal"]:
                    # Actions liées au modal - pas besoin d'action spécifique
                    # Le modal est géré dans MainMenu
                    pass

            elif self.state == "credits":
                action = self.credits_screen.handle_input(event)
                if action == "back_to_menu":
                    self.return_to_menu()

            elif self.state == "how_to_play":
                action = self.how_to_play_screen.handle_input(event)
                if action == "back_to_menu":
                    self.return_to_menu()

            elif self.state == "game":
                if self.game:
                    # Vérifier si le jeu demande de retourner au menu
                    if hasattr(self.game, 'should_return_to_menu') and self.game.should_return_to_menu:
                        self.return_to_menu()
                        return

                    # Passer l'événement au jeu
                    self.game.handle_single_event(event)

    def update(self):
        """Met à jour l'état actuel"""
        dt = self.clock.tick(FPS) / 1000

        if self.state == "credits":
            self.credits_screen.update(dt)
        elif self.state == "game" and self.game:
            self.game.update()
            # Vérifier si le jeu est toujours en cours
            if not self.game.running:
                self.return_to_menu()

    def render(self):
        """Affiche l'écran selon l'état actuel"""
        if self.state == "main_menu":
            self.main_menu.render(self.screen)
        elif self.state == "credits":
            self.credits_screen.render(self.screen)
        elif self.state == "how_to_play":
            self.how_to_play_screen.render(self.screen)
        elif self.state == "game" and self.game:
            self.game.render()

        pg.display.flip()

    def run(self):
        """Boucle principale du gestionnaire de jeu"""
        print("[GAME_MANAGER] Starting game manager")

        while self.running:
            self.handle_events()
            self.update()
            self.render()

        print("[GAME_MANAGER] Game manager stopped")
        pg.quit()


def main():
    try:
        game_manager = GameManager()
        game_manager.run()
    except KeyboardInterrupt:
        print("Game closed by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()