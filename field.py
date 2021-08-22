import os

import pyscroll
import pyscroll.data
from pyscroll.group import PyscrollGroup

from pygame import Rect, JOYAXISMOTION, JOYBUTTONDOWN, JOYBUTTONUP, KEYUP, KEYDOWN
from pygame.locals import K_UP, K_DOWN, K_LEFT, K_RIGHT, K_MINUS, K_PLUS, K_ESCAPE, K_BACKSPACE

from pytmx import load_pygame

from constants import RESOURCE_DIR, RED
from warp_point import WarpPoint
from player import Player
from npc import Npc
from text_edit import TextEdit


class Field(object):
    def __init__(self, name, screen_size):

        self.map_name = name
        self.screen_size = screen_size

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.initialize()

    def initialize(self):

        self.file_path = os.path.join(self.base_dir, RESOURCE_DIR, "maps", self.map_name)
        # load data from pytmx
        self.tmx_data = load_pygame(self.file_path)

        # setup level geometry with simple pygame rects, loaded from pytmx
        self.walls = []
        self.warps = dict()

        for obj in self.tmx_data.objects:
            if obj.type == "warp":
                self.warps[obj.name] = WarpPoint(obj)
            else:
                self.walls.append(Rect(obj.x, obj.y, obj.width, obj.height))

        # create new data source for pyscroll
        self.map_data = pyscroll.data.TiledMapData(self.tmx_data)

        # create new renderer (camera)
        self.map_layer = pyscroll.BufferedRenderer(self.map_data,
                                                   self.screen_size,
                                                   clamp_camera=False,
                                                   tall_sprites=1
                                                   )
        self.map_layer.zoom = 2

        # pyscroll supports layered rendering.  our map has 3 'under' layers
        # layers begin with 0, so the layers are 0, 1, and 2.
        # since we want the sprite to be on top of layer 1, we set the default
        # layer for sprites as 2
        self.group = PyscrollGroup(map_layer=self.map_layer, default_layer=2)

        self.hero_move_speed = 250  # pixels per second

        self.player = Player(self, image="pocky.png")

        self.npc_1 = Npc(self, self.player, "pocky.png", True)

        self.npc_1_position_x = TextEdit("X",
                                         size=32,
                                         color=RED,
                                         width=100,
                                         height=100)

        self.npc_1_position_y = TextEdit("Y",
                                         size=32,
                                         color=RED,
                                         width=100,
                                         height=100)

        # put the hero in the center of the map
        self.player.position = [400, 300]
        self.npc_1.position = [300, 300]

        # add our hero to the group
        self.group.add(self.player)
        self.group.add(self.npc_1)
        self.group.add(self.npc_1_position_x)
        self.group.add(self.npc_1_position_y)

    def update(self, dt):
        self.group.update(dt)

        # check if the sprite's feet are colliding with wall
        # sprite must have a rect called feet, and move_back method,
        # otherwise this will fail
        for sprite in self.group.sprites():
            if isinstance(sprite, Player):
                if sprite.feet.collidelist(self.walls) > -1:
                    sprite.move_back(dt)
                for name, warp in self.warps.items():
                    if sprite.feet.colliderect(warp.get_rect()):
                        self.warps[name].go_inside(self.player)
                    else:
                        self.warps[name].go_outisde()

            elif isinstance(sprite, Npc):
                if sprite.feet.collidelist(self.walls) > -1:
                    sprite.move_back(dt)

            elif isinstance(sprite, TextEdit):
                self.npc_1_position_x.position = [self.player.position[0] + -40, self.player.position[1] - 40]
                self.npc_1_position_y.position = [self.player.position[0] + -40, self.player.position[1] - 60]
                self.npc_1_position_x.text = f"X {self.player.position[0]:.2f}"
                self.npc_1_position_y.text = f"Y {self.player.position[1]:.2f}"

    def draw(self, screen):

        # center the map/screen on our Hero
        self.group.center(self.player.rect.center)

        # draw the map and all sprites
        self.group.draw(screen)

    def handle_input(self, event):

        dead_zone = 0.25

        if event.type == JOYAXISMOTION:
            if event.axis == 0 or event.axis == 1:
                if abs(event.value) > dead_zone:

                    self.player.velocity[event.axis] = event.value * self.hero_move_speed
                else:
                    self.player.velocity[event.axis] = 0
            elif event.axis == 3:
                if event.value > dead_zone or event.value < dead_zone:
                    self.map_layer.zoom += event.value / 10

        elif event.type == JOYBUTTONDOWN:
            if event.button == 2:
                for name, warp in self.warps.items():
                    if warp.get_player():
                        map_name = warp.get_warp_map()
                        print(f"Change Field {map_name}")
                        self.change_field(map_name)

                self.npc_1.shoot()
                self.player.shoot()

        elif event.type == JOYBUTTONUP:
            if event.button == 2:
                pass

        elif event.type == KEYDOWN:
            if event.key == K_LEFT:
                self.player.velocity[0] = -self.hero_move_speed

            elif event.key == K_RIGHT:
                self.player.velocity[0] = self.hero_move_speed

            elif event.key == K_UP:
                self.player.velocity[1] = -self.hero_move_speed

            elif event.key == K_DOWN:
                self.player.velocity[1] = self.hero_move_speed

            # elif event.key == K_BACKSPACE:
            #     if len(self.text) > 0:
            #         self.text = self.text[:-1]
            #         self.text_image = self.font.render(self.text, True, RED)
            #         self.text_rect.size = self.text_image.get_size()
            #         self.text_cursor.topleft = self.text_rect.topright
            # else:
            #     self.text += event.unicode
            #     self.text_image = self.font.render(self.text, True, RED)
            #     self.text_rect.size = self.text_image.get_size()
            #     self.text_cursor.topleft = self.text_rect.topright

        elif event.type == KEYUP:
            if event.key == K_LEFT or event.key == K_RIGHT:
                self.player.velocity[0] = 0
            elif event.key == K_UP or event.key == K_DOWN:
                self.player.velocity[1] = 0

    def add_bullet(self, bullet):
        self.group.add(bullet)

    def change_field(self, name):

        self.map_name = name

        self.initialize()
