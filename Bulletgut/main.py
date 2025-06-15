from engine.game import Game

def main():
    try:
        game = Game()
        game.run()
    except KeyboardInterrupt:
        print("Game closed by user.")

if __name__ == '__main__':
    main()