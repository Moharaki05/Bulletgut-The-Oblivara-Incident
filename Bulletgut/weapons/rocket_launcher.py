from weapons.projectile_weapon import ProjectileWeapon

class RocketLauncher(ProjectileWeapon):
    def __init__(self, game):
        super().__init__(game)
        self.name = "Lance-roquettes"
        self.damage = 100
        self.fire_rate = 0.5
        self.shot_cooldown = 1.0 / self.fire_rate
        self.ammo_type = "rockets"
        self.max_ammo = 10
        self.current_ammo = self.max_ammo
        self.projectile_speed = 250
        self.projectile_lifetime = 10.0
        self.splash_damage = True
        self.splash_radius = 200

        # Charger les sprites
        self.load_sprites([
            "assets/weapons/rocket/idle.png",
            "assets/weapons/rocket/fire1.png",
            "assets/weapons/rocket/fire2.png",
            "assets/weapons/rocket/reload.png"
        ])

        # Sprite du projectile
        self.projectile_sprite = pg.image.load("assets/weapons/rocket/projectile.png").convert_alpha()

        # Sons
        self.fire_sound = pg.mixer.Sound("assets/sounds/rocket_fire.wav")
        self.empty_sound = pg.mixer.Sound("assets/sounds/empty_click.wav")
