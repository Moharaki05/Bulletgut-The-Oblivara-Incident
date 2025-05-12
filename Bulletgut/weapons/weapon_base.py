class Weapon:
    def __init__(self, name, damage, fire_rate, ammo_type, sprite = None):
        self.name = name
        self.damage = damage
        self.fire_rate = fire_rate
        self.ammo_type = ammo_type
        self.sprite = sprite
        self.cooldown = 0

    def update(self, dt):
        self.cooldown = max(0, self.cooldown - dt)

    def can_fire(self):
        return self.cooldown <= 0

    def fire(self, player, world):
        raise NotImplementedError("fire() nust be implemented by subclasses")