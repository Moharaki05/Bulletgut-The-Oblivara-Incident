from engine.game_manager import GameManager

def main():
    try:
        game_manager = GameManager()
        game_manager.run()
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()