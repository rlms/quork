import sys, json, socket, select, random
from operator import attrgetter

from verb_parser import Parser, Verb, Variable, Remainder
import quork_maps
Room = quork_maps.Room

if sys.version_info < (3, 0):
    print("""Python version older than 3.0
The program is unlikely to work, please update.""", file=sys.stderr)

try:
    from enum import Enum
except ImportError:
    print("""Enum module not found.
Some incorrect behaviour may occur.
Try updating to Python 3.4,
or installing the Enum module - `$ pip install enum34`.
""", file=sys.stderr)
    class MetaEnum(type):
        def __new__(cls, clsname, bases, dct):
            return super(MetaEnum, cls).__new__(cls, clsname, bases, dct)
        def __iter__(self):
            for attr in dir(self):
                if not attr.startswith("__"):
                    yield attr
                    
    class Enum(metaclass=MetaEnum):
        pass

DEBUG = False
MOTD = "Welcome to pyTextShooter! Ctrl-c to enter a command. Enter 'help' for a list of commands."

def get_direction(direction, room, no_room, unknown_direction):
    if direction not in Room.directions:
        return (unknown_direction, None)
    elif getattr(room, direction) is None:
        return (no_room, None)
    else:
        return (False, getattr(room, direction))                                                                               

class InjuryCause(Enum):
    shot = 1
    game_rule = 2

class InjuryResult(Enum):
    kill = 1
    no_kill = 2

class Gun:
    max_ammo = None
    normal_damage = None
    headshot_damage = None
    success_message = "You shot {name} for {damage} damage!"
    no_ammo_message = "You don't have any ammo!"
    
    def __init__(self, ammo):
        self.ammo = ammo

    def shoot(self, other, aim_state):
        """
        Attempts to shoot an Entity.
        Returns a message for the shooter.
        """
        if self.ammo > 0:
            self.ammo -= 1
            if aim_state == AimState.head:
                damage = self.headshot_damage
            elif aim_state == AimState.body:
                damage = self.normal_damage
            else:
                return "You aren't aiming at anything the Universe can understand."
            injury_result = other.injure(damage, InjuryCause.shot)
            return (injury_result, self.success_message.format(name=other.name,
                                               damage=damage))
        else:
            return (None, self.no_ammo_message)

    def __repr__(self):
        "{}({})".format(type(self).__name__, self.ammo)

class Rifle(Gun):
    max_ammo = 10
    normal_damage = 20
    headshot_damage = 40            
        

class ItemName:
    def __init__(self, name, article, plural):
        self.name = self.name
        self.article = self.article
        self.plural = plural

    def string(self, plural=False):
        if plural:
            return self.plural
        else:
            return self.article + self.name

    def __repr__(self):
        return "Item({}, {}, {})".format(self.name,
                                         self.kind,
                                         self.plural)

class Item:
    def __init__(self, name):
        self.name = name

class Map:
    def __init__(self, name, rooms, display, description):
        self.name = name
        self.rooms = rooms
        self.display = display
        self.description = description
        

    def __str__(self):
        return self.name

class GameType:
    name = "Base game type"
    rules = "This isn't a real game type"

    @classmethod
    def tick(cls):
        """
        `game.game_type.tick` is run every time the game loops
        """
        pass

class BaseDeathmatch(GameType):
    name = "Base deathmatch game type"
    rules = "Kill to gain points."

    max_kills = 0

    @classmethod
    def tick(cls):
        """
        Detect if anyone has 25 kills, if so declare them the winner.
        """
        for p in Player.players.values():
            if p.kills >= cls.max_kills:
                p.log("Congratulations, you win!")
                for other_p in Player.players.values():
                    if other_p != p:
                        p.log("{} is the winner!".format(p.name))
                for player in Player.players.values():
                    p.die(InjuryCause.game_rule)
                # actually reset the game here

class Deathmatch25(BaseDeathmatch):
    name = "Deathmatch"
    rules = "First to 25 kills."
    max_kills = 25

class Game:
    def __init__(self, game_map, game_type):
        self.map = game_map
        self.game_type = game_type
        Room.rooms = self.map.rooms

    def __repr__(self):
        return "Game({}, {})".format(str(self.map), repr(self.game_type))

class Entity:
    max_health = None
    
    def __init__(self, name, room):
        self.name = name
        self.room = room
        self.reset()

    def reset(self):
        self.health = self.max_health

    def __repr__(self):
        return "{}({}, {})".format(type(self).__name__,
                                   repr(self.name),
                                   repr(self.room))


class AimState(Enum):
    none = 1
    body = 2
    head = 3
    

class Player(Entity):
    players = {}
    
    max_health = 100
    start_ammo = 10

    def __init__(self, name, room):
        super().__init__(name, room)
        self.kills = 0
        self.deaths = 0
        self.data = []
        self.reset()
        Player.players[name] = self

    @staticmethod
    def message_players(players, message, source=None):
        for p in players:
            if p != source:
                p.log(message)

    def log(self, message):
        """
        Logs a message to be sent to the Client the Player belongs to
        """
        self.data.append(message)
        print(message)

    def reset(self):
        self.gun = Rifle(Rifle.max_ammo)
        self.ammo = self.start_ammo
        self.aim_state = AimState.none
        self.target = None
        self.target_room = None
        super().reset()
        

    def in_rooms(self, rooms):
        return any(self.room == room for room in rooms)

    def die(self, cause):
        self.log("You were killed!")
        self.deaths += 1
        self.room = Room.random_room()
        self.reset()
    
    def injure(self, damage, cause):
        self.health -= damage
        self.log("You were shot for {} damage!".format(damage))
        if self.health <= 0:
            self.die(cause)
            return InjuryResult.kill
        else:
            return InjuryResult.no_kill

    def aim_at(self, target, aim_state):
        self.aim_state = aim_state
        self.target = target
        if aim_state == AimState.head:
            self.target_room = target.room
        else:
            self.target_room = None

    def aim_base(self, name, success_message, aim_state):
        unknown_person = "There is nothing called {name}!"
        out_of_range = "{name} is out of range!"
        possible_rooms = self.room.adjacent_rooms() + [self.room]
        if name not in Player.players:
            self.log(unknown_person.format(name=name))
        elif Player.players[name].in_rooms(possible_rooms):
            self.aim_at(Player.players[name], aim_state)
            self.log(success_message.format(name=name))
        else:
            self.log(out_of_range.format(name=name))

    def look_base(self, room):
        self.log(room.name.capitalize())
        self.log(room.description)        

    def update(self):
        """
        Called at the start of each cycle
        """
        if self.aim_state == AimState.head:
            if self.target_room != self.target.room:  # if the target has moved rooms
                self.aim_at(None, AimState.none)
                self.log("Your target has run out of your sights!")
        elif self.aim_state == AimState.body:
            if not self.target.in_rooms(self.room.adjacent_rooms() + [self.room]):
                self.aim_at(None, AimState.none)
                self.log("Your target has run away!")

            
    # The following methods correspond directly to commands.
    # They all return a message for the Player who calls them

    def aim(self, name):
        self.aim_base(name, "You point your gun at {name}!", AimState.body)

    def aim_head(self, name):
        self.aim_base(name, "You point your gun at {name}'s head!", AimState.head)

    def fire(self):
        if self.aim_state != AimState.none:
            # self.update() guarantees a valid, in range target
            old_target = self.target
            result, message = self.gun.shoot(self.target, self.aim_state)
            self.log(message)
            if result is not None:  # shooting was successful
                for p in Player.players.values():
                    if p != self:
                        for d in Room.directions:
                            if getattr(p, d) == self.room:
                                p.log("You hear a loud bang to the {direction}!".format(d.capitalize()))
                        if p.room == self.room:
                            p.log("You hear a loud bang in the room you are in!")
                
            if result == InjuryResult.kill:
                if old_target == self:
                    self.log("You killed yourself!")
                else:
                    self.log("You killed {}!".format(self.target.name))
                    self.target = None
                    self.aim_state = AimState.none
                    self.target_room = None
                    self.kills += 1
        else:
            self.log("You aren't aiming at anything!")

    def reload(self):
        spaces = self.gun.max_ammo - self.gun.ammo
        if self.ammo == 0:
            self.log("You have no ammo left in your pockets!")
        if self.ammo <= spaces:
            self.gun.ammo += self.ammo
            self.ammo = 0
        else:
            self.gun.ammo = self.gun.max_ammo
            self.ammo -= spaces
        self.log("You reloaded {bullets} bullets!".format(bullets=spaces))

    def go(self, direction):
        message, destination = get_direction(direction, self.room,
                                             "You can't go that way!",
                                             "'{}' isn't a direction...".format(direction))
        if destination:
            for p in Player.players.values():
                if p.room == self.room and p != self:
                    p.log("You hear footsteps leaving the room!")
            self.room = destination
            self.log("You went {}!".format(direction))
            for p in Player.players.values():
                if p.room == self.room and p != self:
                    p.log("You hear footsteps entering the room!")
        else:
            self.log(message)

    def look(self):
        self.look_base(self.room)
        for d in Room.directions:
            room = getattr(self.room, d)
            if room:
                self.log("To the {direction} is {room}.".format(direction=d, room=room.name))
                
    def look_direction(self, direction):
        message, room = get_direction(direction, self.room,
                                      "There's nothing in that direction!",
                                      "'{}' isn't a direction".format(direction))
        if room:
            self.look_base(room)
        else:
            self.log(message)

    def info(self):
        self.log("You have {} health".format(self.health))
        self.log("{} ammo in your gun".format(self.gun.ammo))
        self.log("{} ammo in your pocket".format(self.ammo))

    def stats(self):
        self.log("{} kills".format(self.kills))
        self.log("{} deaths".format(self.deaths))

    def say(self, message):
        Player.message_players(Player.players.values(),
                               '{} said "{}"'.format(self.name, message),
                               source=self)

    def tell(self, name, message):
        try:
            Player.players[name].log('{} told you "{}"'.format(self.name,
                                                              message))
        except KeyError:
            self.log("Unknown person '{}'".format(name))

    def set_name_to(self, name):
        if any(c in name for c in "`¬¦!\"£$%^&*()-_=+[{]};:'@#~,<.>/?\\|\n\t "):
            self.log("Names may not contain punctuation or whitespace!")
        elif any(p.name == name for p in Player.players.values()):
            self.log("Someone already has that name!")
        else:
            old_name = self.name
            new_name = name[:3].lower().zfill(3)
            Player.players[new_name] = self
            del Player.players[old_name]
            self.name = new_name
            self.log("Name changed to '{}'!".format(self.name))

    def list_players(self):
        self.log("Players:")
        for name in Player.players:
            self.log(name)

    def display_map(self):
        self.log(game.map.display)

    def rules(self):
        self.log(game.game_type.rules)

    def get_help(self):
        self.log(help_text)               
                

class Verbs(Enum):
    aim = Verb("aim", Variable("name"), desc="aim at someone's body")
    aim_head = Verb("aim", Variable("name"), "head", desc="aim at someone's head")
    fire = Verb("fire", desc="fire at whoever you are aiming at")
    fire.alias("shoot")
    reload = Verb("reload", desc="reload your gun")
    go = Verb("go", Variable("direction"), desc="move to an adjacent room")
    look = Verb("look", desc="look at the room you are in")
    look_direction = Verb("look", Variable("direction"), desc="look into an adjacent room")
    info = Verb("info", desc="get info on your health and inventory")
    stats = Verb("stats", desc="get your kill and death stats")
    say = Verb("say", Remainder("message"), desc="say something to everyone on the server")
    tell = Verb("tell", Variable("name"), Remainder("message"), desc="tell an individual something")
    set_name_to = Verb("set", "name", "to", Variable("name"), desc="change your name")
    list_players = Verb("list", desc="list all online players")
    display_map = Verb("map", desc="display the map")
    get_help = Verb("help", desc="display this")
    rules = Verb("rules", desc="display the rules of the current game")

    @staticmethod
    def verb_name(verb):
        for v in Verbs:
            if verb == v.value:
                return v.name
        else:
            raise ValueError("Unknown verb {}".format(repr(verb)))

    @classmethod
    def generate_help(cls):
        return "\n".join(map(lambda v: str(v.value), cls))

help_text = Verbs.generate_help()

help_text += """
You can only shoot at someone normally in the room you are in, or an adjacent one.
However, you can only shoot someone you are aiming at the head at if they are in the same room they were in when you aimed at them.
Normal shots do 20 damage, and headshots do 40 damage.
"""
    
parser = Parser(list(map(attrgetter("value"), Verbs)))

def send_list(connection, list_):
    bytes_string = bytes(json.dumps(list(list_)), "ascii")
    if len(bytes_string) > 4096:
        raise ValueError("List to send too long")
    while len(bytes_string) < 4096:
       bytes_string += b" "
    connection.send(bytes_string)

def recieve_list(connection):
    return json.loads(connection.recv(4096).decode("ascii").strip())

class Client:
    clients = []
    player_number = 0
    
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address
        while str(Client.player_number).zfill(3) in Player.players:
            Client.player_number += 1
        self.player = Player(str(Client.player_number).zfill(3), Room.random_room())
        Client.clients.append(self)
        self.player.log(MOTD)

    def send_data(self):
        if self.player.data and DEBUG:
            print(self.player.data)
        send_list(self.connection, ["\n".join(self.player.data)])
        self.player.data = []
        

    def get_command(self):
        command = recieve_list(self.connection)[0]
        if DEBUG:
            print(command)
        result = parser.parse(command)
        if result is not None:
            verb, variables = result
            verb_name = Verbs.verb_name(verb)
            getattr(self.player, verb_name)(**variables)
            # e.g. if verb is `Verbs.aim_head.value`, then this calls `self.aim_head(name=variables["name"])`
        else:
            similar = [v.value for v in Verbs if command.startswith(v.value.words[0])]
            if similar:
                for s in similar:
                    self.player.log("Did you mean '{}'?".format(str(s)))
            self.player.log("Unknown command '{}'".format(command))
        

    def __repr__(self):
        return "Client({}, {}, {})".format(repr(self.connection),
                                           repr(self.address),
                                           repr(self.player))

# currently irrelevant	
def grue_name(grue_names=[]):
    letters = "rhgmnsz"
    while True:
        name = "".join(random.choice(letters) for _ in range(3))
        if name not in grue_names:
            grue_names.append(name)
            return name

def delete_client(client):
    print("A client disconnected :-(")
    Client.clients.remove(client)
    del Player.players[client.player.name]

game = Game(Map("Beige", quork_maps.beige_rooms, quork_maps.beige_display, "A small, bland map."),
            Deathmatch25)

print(socket.gethostbyname(socket.gethostname()))

HOST = ''
PORT = 13337
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))

s.listen(1)

Client(*s.accept())
print("The first player joined!")
s.settimeout(0)

while True:
    try:
        Client(*s.accept())
        print("A new player joined!")
        for p in Player.players.values():
            if p != Client.clients[-1].player:
                p.log("A new player joined!")
    except IOError:
        pass

    game.game_type.tick()

    for c in Client.clients:
        c.player.update()
    
    for c in Client.clients:
        readable, writable, exceptional = select.select([c.connection], [c.connection], [], 0.1)
        if readable:
            try:
                c.get_command()
            except ConnectionResetError:
                delete_client(c)
                continue
    
            
        if writable:
            try:
                c.send_data()
            except ConnectionResetError:
                delete_client(c)
                continue
            
