import pygame as pg
from engine.game import Game
from ui.main_menu import MainMenu
from ui.credits import CreditsScreen
from ui.how_to_play import HowToPlayScreen
from ui.loading import LoadingScreen
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
        self.state = "main_menu"  # "main_menu", "loading", "game", "credits", "how_to_play"

        # Initialiser les écrans
        self.main_menu = MainMenu()
        self.credits_screen = CreditsScreen()
        self.how_to_play_screen = HowToPlayScreen()
        self.loading_screen = LoadingScreen()
        self.game = None
        self.game_ready = False

        # ⭐ NOUVEAU : Surface pour stocker le rendu du jeu
        self.game_surface = None

        # Contrôle de la souris pour les menus
        pg.event.set_grab(False)
        pg.mouse.set_visible(True)

        # ⭐ NOUVEAU : Initialiser le menu principal avec la musique
        print("[GAME_MANAGER] Initializing main menu with music")
        self.main_menu.show()

    def start_loading(self):
        """Démarre l'écran de chargement avant de lancer le jeu"""
        try:
            print("[GAME_MANAGER] Starting loading screen")
            self.state = "loading"
            self.loading_screen.start_loading()
        except Exception as e:
            print(f"[GAME_MANAGER] Error starting loading screen: {e}")
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

        # ⭐ NOUVEAU : Reset du flag game_ready et de la surface
        self.game_ready = False
        self.game_surface = None

        self.state = "main_menu"
        self.main_menu.show()  # ⭐ Appel explicite pour relancer la musique du menu
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
                    self.start_loading()  # Commencer par l'écran de chargement
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

        if self.state == "loading":
            self.loading_screen.update(dt)

            # Vérifier si le chargement est terminé
            if self.loading_screen.is_complete and not self.game_ready:
                print("[GAME_MANAGER] Creating game during loading completion")
                try:
                    # Créer le jeu silencieusement (sans changer de state)
                    self.game = Game(self.screen)
                    self.game_ready = True
                    print("[GAME_MANAGER] Game created and ready")

                    # ⭐ NOUVEAU : Rendre le jeu immédiatement pour préparer la transition
                    self.prepare_game_surface()

                except Exception as e:
                    print(f"[GAME_MANAGER] Error creating game: {e}")
                    self.return_to_menu()
                    return

            # Vérifier si le chargement ET la transition rideau sont terminés
            if self.loading_screen.is_finished():
                print("[GAME_MANAGER] Loading and transition complete, switching to game state")
                self.switch_to_game_state()

        elif self.state == "credits":
            self.credits_screen.update(dt)

        elif self.state == "game" and self.game:
            self.game.update()
            # Vérifier si le jeu est toujours en cours
            if not self.game.running:
                self.return_to_menu()

    def prepare_game_surface(self):
        """Prépare la surface du jeu pour la transition rideau"""
        if self.game and self.game_ready:
            print("[GAME_MANAGER] Preparing game surface for transition")
            # Créer une surface temporaire pour capturer le rendu du jeu
            temp_surface = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

            # Sauvegarder la surface actuelle
            original_screen = self.game.screen

            # Temporairement rediriger le rendu vers notre surface
            self.game.screen = temp_surface

            # Rendre le jeu sur notre surface temporaire
            self.game.render()

            # Restaurer la surface originale
            self.game.screen = original_screen

            # Sauvegarder la surface du jeu
            self.game_surface = temp_surface.copy()
            print("[GAME_MANAGER] Game surface prepared")

    def switch_to_game_state(self):
        """Passe au state 'game' après la transition"""
        # Activer le contrôle souris pour le jeu
        pg.event.set_grab(True)
        pg.mouse.set_visible(False)

        self.state = "game"
        print("[GAME_MANAGER] Switched to game state")

    def render(self):
        """Affiche l'écran selon l'état actuel"""
        if self.state == "main_menu":
            self.main_menu.render(self.screen)
        elif self.state == "loading":
            # ⭐ NOUVEAU : Gérer la transition rideau avec le jeu en arrière-plan
            if self.loading_screen.curtain_transition and self.game_surface:
                # D'abord, afficher le jeu en arrière-plan
                self.screen.blit(self.game_surface, (0, 0))
                # Puis appliquer l'effet rideau par-dessus
                self.loading_screen.render(self.screen)
            else:
                # Affichage normal de l'écran de chargement
                self.loading_screen.render(self.screen)
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