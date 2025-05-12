from engine.game import Game
from pytmx import load_pygame

def main():
    try:
        game = Game()

        tmx = load_pygame("assets/maps/test_level.tmx")

        game.run()
    except KeyboardInterrupt:
        print("Game closed by user.")

if __name__ == '__main__':
    main()