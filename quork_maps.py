import random

class Room:
    directions = ("north", "south", "east", "west")
    rooms = {}
    
    def __init__(self, name, objects, description,
                 north=None,west=None,south=None,east=None):
        self.name = name
        self.objects = objects
        self.description = description
        self._north = north
        self._west = west
        self._south = south
        self._east = east

    def _get_room(self, direction):
        try:
            return Room.rooms[getattr(self, "_"+direction)]
        except KeyError:
            return None

    @property
    def north(self):
        return self._get_room("north")
        
    @north.setter
    def north(self, value):
        self._north = value

    @property
    def west(self):
        return self._get_room("west")

    @west.setter
    def west(self, value):
        self._west = value

    @property
    def south(self):
        return self._get_room("south")

    @south.setter
    def south(self, value):
        self._south = value

    @property
    def east(self):
        return self._get_room("east")

    @east.setter
    def east(self, value):
        self._east = value
        
    def adjacent_rooms(self):
        return [getattr(self, direction) for direction in Room.directions]

    @classmethod
    def random_room(self):
        return random.choice(list(Room.rooms.values()))
        
    def __repr__(self):
        return "Room({}, {}, {}, north={}, west={}, south={}, east={})".format(*map(repr, (self.name,
                                                                                           self.objects,
                                                                                           self.description,
                                                                                           self._north,
                                                                                           self._west,
                                                                                           self._south,
                                                                                           self._east)))


beige_display =\
"""                      Store room
                            |
Mirror corridor----------Laboratory---Green wallpaper corridor
     |                                      |
Boat painting corridor---Office-------Bin corridor
     |                      |               |
Cactus corridor----------Fountain-----Orange wallpaper corricor
     |                      |               |
Featureless corridor-----Library------Window corridor
     |                                      |
Fish corridor------------Kitchen------Carpetless corridor
                            |
                         Toilet"""

beige_rooms = {
        "laboratory": Room("the laboratory",[],
                      "A disused laboratory. It's all sciencey.",
                      north="store room",west="corridor1",east="corridor2"),
        "store room": Room("the store room",[],
                      "An empty store room. Out of a window, you can see a distant hill.",
                      south="laboratory"),
        "corridor1": Room("a corridor",[],
                      "On the wall is a large mirror.",
                      east="laboratory",south="corridor3"),
        "corridor2": Room("a corridor",[],
                      "The wallpaper is green and tasteless.",
                      west="laboratory",south="corridor4"),
        "corridor3": Room("a corridor",[],
                      "A painting of a boat is on the wall.",
                      north="corridor1",east="office",south="corridor5"),
        "corridor5": Room("a corridor",[],
                      "A cactus is mounted on the wall.",
                      north="corridor3",east="fountain",south="corridor7"),
        "corridor7": Room("a corridor",[],
                      "It has no features.",
                      north="corridor5",east="library",south="corridor9"),
        "corridor9": Room("a corridor",[],
                      "A fish is stuck to the wall with a spike.",
                      north="corridor7",east="kitchen"),
        "corridor4": Room("a corridor",[],
                      "A bin is here.",
                      north="corridor2",west="office",south="corridor6"),
        "corridor6": Room("a corridor",[],
                      "A corridor. The wallpaper is orange and smells.",
                      north="corridor4",west="fountain",south="corridor8"),
        "corridor8": Room("a corridor",[],
                      "Out of a window, you can see a distant valley.",
                      north="corridor6",west="library",south="corridor10"),
        "corridor10": Room("a corridor",[],
                      "It has no carpet.",
                      north="corridor8",west="kitchen"),
        "office": Room("the office",[],
                      "An office. A desk with papers all over it is in the corner. It feels Kafkaesque.",
                      west="corridor3",east="corridor4",south="fountain"),
        "fountain": Room("the room with a fountain",[],
                      "A room with an ornate, but broken fountain in it. It feels somewhat central.",
                      north="office",west="corridor5",east="corridor6",south="library"),
        "library": Room("the library",[],
                      "A library, with bookshelves lining the walls. On close inspection, all the books are biographies of Morrissey.",
                      north="fountain",west="corridor7",east="corridor8"),
        "kitchen": Room("the kitchen",[],
                      "An old kitchen, with what looks like old cooking equipment in it (surprising!)",
                      south="toilet",west="corridor9",east="corridor10"),
        "toilet": Room("a toilet",[],
                      "A toilet, with a broken sink. There is some inane graffiti on the wall.",
                      north="kitchen")
        }
