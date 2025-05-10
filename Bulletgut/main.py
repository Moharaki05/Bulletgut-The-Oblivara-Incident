from engine.game import Game
from pytmx import load_pygame

def main():
    try:
        game = Game()

        tmx = load_pygame("assets/maps/test_level.tmx")
        print("Checking door objects...")
        for obj in tmx.objects:
            if obj.type == "door":
                gx = int(obj.x // tmx.tilewidth)
                gy = int(obj.y // tmx.tileheight)
                print(f"Door at ({gx}, {gy}), properties: {obj.properties}")

        game.run()
    except KeyboardInterrupt:
        print("Game closed by user.")

if __name__ == '__main__':
    main()