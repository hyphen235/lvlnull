from pathlib import Path
from arcade.experimental import Shadertoy
import arcade
import math
import arcade.gui
from arcade.gui import UIManager
from arcade.gui.widgets import UITextArea, UITexturePane
from arcade.experimental.lights import Light, LightLayer
from PlayerCharacter import PlayerCharacter
from constants import *
from Enemy import Enemy
from EnemyFactory import enemy_factory


def load_texture_pair(filename):
    '''loading our texture pair'''
    return [
        arcade.load_texture(filename),
        arcade.load_texture(filename, flipped_horizontally=True),
    ]


class MenuView(arcade.View):
    '''Sets the main menu view when you start the game'''

    def __init__(self):
        super().__init__()
        self.background = None
        self.text = "Level.Null()"
        self.manager = arcade.gui.UIManager()
        self.manager.enable()
        self.v_box = arcade.gui.UIBoxLayout()
        start_button = arcade.gui.UIFlatButton(text="Start Game", width=150)
        self.v_box.add(start_button.with_space_around(bottom=20))
        start_button.on_click = self.on_click_start

        # Create a widget to hold the v_box widget, that will center the buttons
        self.manager.add(
            arcade.gui.UIAnchorWidget(
                allign_x=SCREEN_WIDTH / 2,
                allign_y=SCREEN_HEIGHT / 2 - 400,
                child=self.v_box,
            )
        )
    # Checks if start button has been pressed, and will start the game if it has.

    def on_click_start(self, event):
        print("Start:", event)
        self.window.show_view(self.game_view)
        self.window.set_mouse_visible(False)

    # Loads the background for the menu
    def on_show_view(self):
        self.background = arcade.load_texture("assets\menu.png")
        self.game_view = MyGame()
        self.game_view.setup()

    # Draws the menu, the title, buttons etc.
    def on_draw(self):
        self.clear()
        arcade.draw_lrwh_rectangle_textured(
            0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, self.background
        )
        arcade.draw_text(
            self.text,
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT / 2 + 150,
            arcade.color.WHITE,
            font_size=56,
            font_name="Kenney Pixel",
            anchor_x="center",
        )
        self.manager.draw()


class LoseView(arcade.View):
    '''Custom class for when the player loses.'''

    def __init__(self):
        super().__init__()
        self.text = "Game Over"
        self.background = None

    # Loads the background image.
    def on_show_view(self):
        self.background = arcade.load_texture("assets\SPOOKY GAME OVER.png")
        self.game_view = MyGame()
        self.game_view.setup()

    def on_draw(self):
        self.clear()
        arcade.draw_lrwh_rectangle_textured(
            0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, self.background
        )
        # Draws the "Game Over" text
        arcade.draw_text(
            self.text,
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT / 2,
            arcade.color.WHITE,
            font_size=40,
            anchor_x="center",
            font_name="Kenney Pixel",
        )
    # Checks for mouse press on lose screen, if mouse is pressed, the game restarts.

    def on_mouse_press(self, _x, _y, _button, _modifiers):
        self.window.show_view(self.game_view)


class MyGame(arcade.View):
    '''Class for the entire game view and everything inside it.'''

    def __init__(self):

        super().__init__()
        self.manager = UIManager()
        self.manager.enable()
        bg_tex = arcade.load_texture("assets/txtbox.png")
        self.text_area = UITextArea(
            x=SCREEN_WIDTH / 2 - 315,
            y=25,
            width=600,
            height=200,
            text="",
            text_color=(255, 255, 255, 255),
        )
        self.manager.add(
            UITexturePane(
                self.text_area.with_space_around(right=20),
                tex=bg_tex,
                padding=(10, 10, 10, 10),
            )
        )
        # Our long list of variables.
        self.shadertoy = None
        self.channel0 = None
        self.channel1 = None
        self.load_shader()
        self.obj_alpha = 0
        self.text_alpha = 255
        self.esc_alpha = 255
        self.box_alpha = 0
        self.levelnum = 0
        self.sanity_alpha = 0
        self.lights_on = None
        self.player_list = None
        self.enemy_list = None
        self.torso_list = None
        self.torso_sprite = None
        self.cursor_list = None
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False
        self.shift_pressed = False
        self.light_layer = None
        self.player_light = None
        self.scene = None
        self.physics = None
        self.camera = None
        self.HUD_camera = None
        self.sprint_bar = None
        self.sprintbarback = None
        self.sprintbarfore = None
        self.level = 2
        self.facesoundvol = 0.2
        self.subtitle = None
        self.escpressed = False
        self.sanity = False
        self.sanity_img = None
        self.lighthum = None
        self.lvl1mus = arcade.load_sound("assets/sounds/Level.Null.mp3")
        self.lvl2mus = arcade.load_sound("assets/sounds/scary.mp3")
        self.lvl5mus = arcade.load_sound("assets/sounds/fin.mp3")
        self.humsound = arcade.load_sound("assets/sounds/light hum.mp3")
        self.music = arcade.play_sound(self.lvl1mus, 0.0, looping=True)
        self.lighthum = arcade.play_sound(self.humsound, 0.0, looping=True)
        self.wavesound = arcade.load_sound("assets\sounds\waves.mp3")
        self.footstepsound = arcade.load_sound(
            "assets/sounds/bary_footstep_carpet1.mp3"
        )
        self.footstep = arcade.play_sound(
            self.footstepsound, 0.0, looping=False)
        arcade.set_background_color(arcade.color_from_hex_string("#7b692f"))

    def load_shader(self):
        '''Raycast shader from arcade documentation https://api.arcade.academy/en/latest/tutorials/raycasting/index.html'''
        # Where is the shader file? Must be specified as a path.
        shader_file_path = Path("shadeer.glsl")
        window_size = [SCREEN_WIDTH, SCREEN_HEIGHT]

        # Create the shader toy
        self.shadertoy = Shadertoy.create_from_file(
            window_size, shader_file_path)

        # Create the channels 0 and 1 frame buffers.
        # Make the buffer the size of the window, with 4 channels (RGBA)
        self.channel0 = self.shadertoy.ctx.framebuffer(
            color_attachments=[self.shadertoy.ctx.texture(
                window_size, components=4)]
        )
        self.channel1 = self.shadertoy.ctx.framebuffer(
            color_attachments=[self.shadertoy.ctx.texture(
                window_size, components=4)]
        )

        # Assign the frame buffers to the channels
        self.shadertoy.channel_0 = self.channel0.color_attachments[0]
        self.shadertoy.channel_1 = self.channel1.color_attachments[0]

    def setup(self):
        '''Sets up all of the assets and scene'''
        # Creates and hashes the layers for the game view.
        layer_options = {
            "spawn": {"custom_class": PlayerCharacter, "custom_class_args": {}},
            "walls": {"use_spatial_hash": True},
            "doors": {"use_spatial_hash": True},
            "floor": {"use_spatial_hash": True},
            "details": {"use_spatial_hash": True},
            "lights": {"use_spatial_hash": True},
        }

        # Function used to load the maps.
        tile_map = arcade.load_tilemap(
            # Uses level number to differentiate the levels.
            f"Level {self.level} assets\lvl{self.level}.tmx",
            TILE_SCALING,
            layer_options=layer_options,
        )
        # Creates our lists.
        self.scene = arcade.Scene.from_tilemap(tile_map)
        self.player_list = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList()
        self.door_list = self.scene["doors"]
        self.door_list = arcade.SpriteList()
        self.door_list = self.scene["doors"]
        self.scene.add_sprite_list("player_list")
        self.scene.add_sprite_list("torso_list")
        self.scene.add_sprite_list("enemy_list")
        self.cursor_list = arcade.SpriteList()

        # loads assets for the ui
        self.sprintbarback = arcade.load_texture("assets/sprintbarback.png")
        self.sprintbarfore = arcade.load_texture("assets/sprintbarfore.png")
        self.sanity_img = arcade.load_texture("assets/sanity.png")

        #  loads sprites for the player and cursor and appends them to the scene
        torso = f"./assets/dude.png"
        self.torso_sprite = arcade.Sprite(torso, CHARACTER_SCALING)
        self.scene["torso_list"].append(self.torso_sprite)
        self.torso_sprite.angle = 180
        cursor = f"./assets/cursor.png"
        self.cursor_sprite = arcade.Sprite(cursor, CURSOR_SCALING)
        self.cursor_list.append(self.cursor_sprite)
        self.player_sprite = self.scene["spawn"][0]
        self.scene["player_list"].append(self.player_sprite)
        self.light_layer = LightLayer(SCREEN_WIDTH, SCREEN_HEIGHT)
        #  spawns enemies at their spawn points
        for spawn_point in self.scene["enemy_spawn"]:
            self.scene["enemy_list"].append(enemy_factory(spawn_point))

        # Creates physics engines to handle collision with walls, enemies and player.
        self.physics_engine = arcade.PhysicsEngineSimple(
            self.player_sprite, walls=[self.scene["walls"], self.door_list]
        )
        self.enemy_physics_engines = []
        for enemy in self.scene["enemy_list"]:
            engine = arcade.PhysicsEngineSimple(
                enemy, walls=[self.scene["walls"], self.door_list]
            )
            self.enemy_physics_engines.append(engine)

        # Creates camera to follow the player.
        for sprite in self.scene["exit"]:
            self.camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
            self.HUD_camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

        # loads music for individual levels.
        if self.level == 1:
            arcade.stop_sound(self.music)
            self.music = arcade.play_sound(self.lvl1mus, 0.2, looping=True)
            self.lighthum = arcade.play_sound(self.humsound, 0.2, looping=True)
        elif self.level == 2:
            arcade.stop_sound(self.music)
            arcade.stop_sound(self.lighthum)
            self.music = arcade.play_sound(self.lvl2mus, 0.2, looping=True)
        elif self.level == 3:
            arcade.stop_sound(self.music)
            self.music = arcade.play_sound(self.lvl1mus, 0.2, looping=True)
            self.lighthum = arcade.play_sound(self.humsound, 1, looping=True)
        elif self.level == 5:
            arcade.stop_sound(self.music)
            arcade.stop_sound(self.lighthum)
            self.music = arcade.play_sound(self.lvl5mus, 0.2, looping=True)
            self.lighthum = arcade.play_sound(
                self.wavesound, 0.2, looping=True)

        # Turns lights off for level 2, since the player must turn the power on.
        if self.level == 2:
            self.lights_on = False
        else:
            self.lights_on = True

        if self.lights_on == True:
            for sprite in self.scene["lights"]:
                light = Light(
                    sprite.center_x,
                    sprite.center_y,
                    sprite.properties["radius"],
                    color=sprite.properties["color"][:3],
                    mode="soft",
                )
                self.light_layer.add(light)

        # creates the player light
        self.player_light = Light(
            self.torso_sprite.center_x, self.torso_sprite.center_y, 300, arcade.color_from_hex_string(
                "#363636"), "soft"
        )
        self.light_layer.add(self.player_light)

    def on_draw(self):
        '''Draws the scene'''

        # sets the camera up and uses channnel 0 for raycasting shadows
        self.clear()
        self.camera.use()
        self.channel0.use()
        self.channel0.clear()
        self.scene["walls"].draw()

        # draws the lights
        with self.light_layer:
            self.clear()
            self.scene.draw()
        self.light_layer.draw()

        # Makes sure the raycast starts at the player origin
        p = (
            self.player_sprite.position[0] - self.camera.position[0],
            self.player_sprite.position[1] - self.camera.position[1],
        )
        self.shadertoy.program["lightPosition"] = p
        self.shadertoy.program["lightSize"] = 3000
        self.shadertoy.render()

        # draws all of the ui assets without shading
        self.HUD_camera.use()
        self.cursor_list.draw()
        self.manager.draw()
        sprint_bar_color = arcade.color_from_hex_string("#bdbdbd")
        if self.player_sprite.resting:
            sprint_bar_color = arcade.color_from_hex_string("#703832")
        self.cursor_list.draw()
        arcade.draw_lrwh_rectangle_textured(6, 6, 28, 357, self.sprintbarback)
        arcade.draw_lrtb_rectangle_filled(
            10,
            30,
            (SCREEN_HEIGHT - 610) * self.player_sprite.stamina / 100 + 11,
            10,
            sprint_bar_color,
        )
        arcade.draw_lrwh_rectangle_textured(6, 6, 26, 357, self.sprintbarfore)
        if self.sanity:
            arcade.draw_lrwh_rectangle_textured(
                0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, self.sanity_img, alpha=150
            )
        # lerp function for fading text
        self.text_alpha = int(arcade.utils.lerp(self.text_alpha, 0, 0.005))
        self.obj_alpha = int(arcade.utils.lerp(self.obj_alpha, 255, 0.01))
        self.esc_alpha = int(arcade.utils.lerp(self.esc_alpha, 0, 0.005))

        # draws all of the text on screen
        arcade.draw_text(
            f"Level {self.levelnum} : {self.subtitle}",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT / 2 + 125,
            color=(255, 255, 255, self.text_alpha),
            font_size=36,
            anchor_x="center",
            font_name="Kenney Pixel",
        )
        if self.escpressed == True:
            arcade.draw_text(
                "There is no escape.",
                SCREEN_WIDTH,
                SCREEN_HEIGHT - 30,
                color=(255, 255, 255, self.esc_alpha),
                font_size=28,
                anchor_x="right",
                font_name="Kenney Pixel",
            )

        # sets subtitle text
        if self.level == 1:
            self.levelnum = 0
            self.subtitle = "'The Lobby'"
        if self.level == 2:
            self.levelnum = 1
            self.subtitle = "'Habitable Zone'"
        if self.level == 3:
            self.levelnum = 2
            self.subtitle = "'Pipe Dreams'"
        if self.level == 4:
            self.levelnum = 3
            self.subtitle = "'Electrical Station'"
        if self.level == 5:
            self.levelnum = 100
            self.subtitle = "'Silent Waves'"

    def process_keychange(self):
        '''processes the keyboard inputs'''

        sprint_speed = SPRINT_SPEED

        # handles the player no longer sprinting
        if self.player_sprite.resting:
            self.player_sprite.sprinting = False

        # processes keyboard input into movement , makes sure sound is played when the player moves and makes the legs move in the correct direction
        if self.up_pressed and not self.down_pressed:
            self.player_sprite.change_y = (
                PLAYER_MOVEMENT_SPEED + sprint_speed * self.player_sprite.sprinting
            )
            self.player_sprite.angle = 90
            arcade.stop_sound(self.footstep)
            self.footstep = arcade.play_sound(
                self.footstepsound, 1, looping=True)
        elif self.down_pressed and not self.up_pressed:
            self.player_sprite.change_y = (
                -PLAYER_MOVEMENT_SPEED + -sprint_speed * self.player_sprite.sprinting
            )
            self.player_sprite.angle = -90
            arcade.stop_sound(self.footstep)
            self.footstep = arcade.play_sound(
                self.footstepsound, 1, looping=True)
        else:
            self.player_sprite.change_y = 0
            arcade.stop_sound(self.footstep)
        if self.right_pressed and not self.left_pressed:
            self.player_sprite.change_x = (
                PLAYER_MOVEMENT_SPEED + sprint_speed * self.player_sprite.sprinting
            )
            self.player_sprite.angle = 0
            arcade.stop_sound(self.footstep)
            self.footstep = arcade.play_sound(
                self.footstepsound, 1, looping=True)
        elif self.left_pressed and not self.right_pressed:
            self.player_sprite.change_x = (
                -PLAYER_MOVEMENT_SPEED + -sprint_speed * self.player_sprite.sprinting
            )
            self.player_sprite.angle = 0
            arcade.stop_sound(self.footstep)
            self.footstep = arcade.play_sound(
                self.footstepsound, 1, looping=True)
        else:
            self.player_sprite.change_x = 0

    def on_key_press(self, key, modifiers):
        '''Handles key pressed state with booleans'''
        if key == arcade.key.W:
            self.up_pressed = True
        elif key == arcade.key.S:
            self.down_pressed = True
        elif key == arcade.key.A:
            self.left_pressed = True
        elif key == arcade.key.D:
            self.right_pressed = True

        if key == arcade.key.ESCAPE:
            self.esc_alpha = 255
            self.escpressed = True

        if key == arcade.key.SPACE:
            if self.player_light in self.light_layer:
                self.light_layer.remove(self.player_light)
            else:
                self.light_layer.add(self.player_light)

        # bitwise and of modifier keys. See https://api.arcade.academy/en/latest/keyboard.html#keyboard-modifiers
        self.player_sprite.sprinting = modifiers and arcade.key.MOD_SHIFT

        self.process_keychange()

    def on_key_release(self, key, modifiers):
        '''Handles key released state with booleans'''

        if key == arcade.key.W:
            self.up_pressed = False
            arcade.stop_sound(self.footstep)
        if key == arcade.key.S:
            self.down_pressed = False
            arcade.stop_sound(self.footstep)
        elif key == arcade.key.A:
            self.left_pressed = False
            arcade.stop_sound(self.footstep)
        elif key == arcade.key.D:
            self.right_pressed = False
            arcade.stop_sound(self.footstep)

        # bitwise and of modifier keys. See https://api.arcade.academy/en/latest/keyboard.html#keyboard-modifiers
        self.player_sprite.sprinting = modifiers and arcade.key.MOD_SHIFT

        self.process_keychange()

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        self.handle_interact()

    def handle_interact(self):
        '''interaction handling using function in on mouse press'''

        objects = arcade.check_for_collision_with_list(
            self.player_sprite, self.scene["Interactables"]
        )

        for interactable in objects:
            getattr(self, interactable.properties["oninteract"])(interactable)

    def toggle_switch(self, interactable):
        '''handles the switch being toggled and then opens gates and turns on lights on level 2'''

        switches = (
            l for l in self.scene["Interactables"] if l.properties["type"] == "switch"
        )
        toggled = not interactable.properties["toggled"]
        for switch in switches:
            switch.properties["toggled"] = toggled
            if toggled:
                switch.texture = arcade.load_texture(f"assets\leverdown.png")
            else:
                switch.texture = arcade.load_texture(f"assets\leverup.png")

        if toggled and self.level == 2:
            for sprite in self.scene["lights"]:
                light = Light(
                    sprite.center_x,
                    sprite.center_y,
                    sprite.properties["radius"],
                    color=sprite.properties["color"][:3],
                    mode="soft",
                )
                self.light_layer.add(light)
                self.light_layer.remove(self.player_light)
                self.light_layer.add(self.player_light)

        #  makes doors open when switch is toggled
        for door in self.scene["doors"]:
            door.properties["toggled"] = toggled
            if toggled:
                self.scene["doors"].clear()

        if self.level == 2:
            self.text_area.text = (
                "The power is back on, maybe the gates have been opened."
            )

    def draw_text(self, interactable):
        self.text_area.text = interactable.properties["text"]

    def center_camera_to_player(self):
        '''centers the camera to the center of the player'''
        screen_center_x = self.player_sprite.center_x - \
            (self.camera.viewport_width / 2)

        screen_center_y = self.player_sprite.center_y - (
            self.camera.viewport_height / 2
        )
        player_centered = screen_center_x, screen_center_y
        self.camera.move_to(player_centered)

    def on_update(self, delta_time):
        '''updates all of the line of sight code and physics engines'''

        self.center_camera_to_player()

        # joins the torso to the legs and maps cursor coords to mouse
        self.torso_sprite.center_x = self.player_sprite.center_x
        self.torso_sprite.center_y = self.player_sprite.center_y
        self.torso_sprite.update()
        self.player_sprite.update(delta_time)
        self.cursor_sprite.center_x = self.window._mouse_x
        self.cursor_sprite.center_y = self.window._mouse_y

        # updates enemies moving and collisions
        for engine in self.enemy_physics_engines:
            engine.update()

        if arcade.check_for_collision_with_list(
            self.player_sprite, self.scene["enemy_list"]
        ):
            arcade.stop_sound(self.music)
            arcade.stop_sound(self.lighthum)
            self.window.show_view(self.window.lose_view)

        # changes level when colliding with exit
        if arcade.check_for_collision_with_list(
            self.player_sprite, self.scene["exit"], method=1
        ):
            self.level += 1
            self.text_alpha = 255
            self.setup()
        start_x = self.torso_sprite.center_x
        start_y = self.torso_sprite.center_y
        dest_x = self.camera.position.x + self.window._mouse_x
        dest_y = self.camera.position.y + self.window._mouse_y
        x_diff = dest_x - start_x
        y_diff = dest_y - start_y
        angle = math.atan2(y_diff, x_diff)
        self.torso_sprite.angle = math.degrees(angle) - 90

        # line of sight and enemie looking code
        self.sanity = False
        for enemy in self.scene["enemy_list"]:
            if arcade.has_line_of_sight(
                self.player_sprite.position, enemy.position, self.scene["walls"], 350
            ):
                self.sanity = True
                enemy.follow_sprite(self.player_sprite)
                start_x = enemy.center_x
                start_y = enemy.center_y
                dest_x = self.torso_sprite.center_x
                dest_y = self.torso_sprite.center_y
                x_diff = dest_x - start_x
                y_diff = dest_y - start_y
                angle = math.atan2(y_diff, x_diff)
                enemy.angle = math.degrees(angle) - 90
                enemy.change_x = math.cos(angle) * SPRITE_SPEED
                enemy.change_y = math.sin(angle) * SPRITE_SPEED
            else:
                enemy.change_x = 0
                enemy.change_y = 0
                enemy.random_move()

        # puts the player light at the player
        self.player_light.position = self.torso_sprite.position

        # updates player physics engine
        self.physics_engine.update()


def main():
    '''draws the menu, lose and game views'''
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.menu_view = MenuView()
    window.lose_view = LoseView()
    window.show_view(window.menu_view)
    arcade.run()


if __name__ == "__main__":
    main()
