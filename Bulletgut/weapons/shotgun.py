from weapons.hitscan_weapon import HitscanWeapon

class Shotgun(HitscanWeapon):
    def __init__(self, game):
        super().__init__(game)
        self.name = "Shotgun"
        self.damage = 8  # Par pellet
        self.fire_rate = 1.0
        self.shot_cooldown = 1.0 / self.fire_rate
        self.spread = 0.15
        self.pellets = 8
        self.ammo_type = "shells"
        self.max_ammo = 25
        self.current_ammo = self.max_ammo

        # Charger les sprites
        self.load_sprites([
            "assets/weapons/shotgun/idle.png",
            "assets/weapons/shotgun/fire1.png",
            "assets/weapons/shotgun/fire2.png",
            "assets/weapons/shotgun/reload1.png",
            "assets/weapons/shotgun/reload2.png"
        ])

        # Sons
        self.fire_sound = pg.mixer.Sound("assets/sounds/shotgun_fire.wav")
        self.reload_sound = pg.mixer.Sound("assets/sounds/shotgun_reload.wav")
        self.empty_sound = pg.mixer.Sound("assets/sounds/empty_click.wav")
