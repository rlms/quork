class Variable:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "[{}]".format(self.name)

    def __repr__(self):
        return "Variable({})".format(repr(self.name))

class Remainder:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "[{}]".format(self.name)

    def __repr__(self):
        return "Remainder({})".format(repr(self.name))

class Verb:
    def __init__(self, *words, desc=""):
        self.words = words
        self.aliases = []
        self.desc = desc#ription

    def alias(self, *words):
        self.aliases.append(Verb(*words))

    def match(self, words):
        try:
            variables = {}
            if len(self.words) != len(words) and not any(isinstance(p, Remainder) for p in self.words):
                raise Parser.ParseError("Command '{}' has a different amount of words to the pattern that matches it".format(words))
            
            for index, (a, b) in enumerate(zip(self.words, words)):
                if isinstance(a, Variable):
                    variables[a.name] = b
                elif isinstance(a, str):
                    if a != b:
                        raise Parser.ParseError("'{}' does not match '{}'".format(a, b))
                elif isinstance(a, Remainder):
                    variables[a.name] = " ".join(words[index:])
                    break
                else:
                    raise Parser.ParseError("Invalid verb part {}".format(repr(a)))
                
            return (self, variables)
        except Parser.ParseError:
            for alias in self.aliases:
                try:
                    return (self, alias.match(words)[-1])
                except Parser.ParseError:
                    raise
            else:
                raise Parser.ParseError("Unmatched verb")

    def __str__(self):
        return " ".join(map(str, self.words)) + " - " + self.desc

    def __repr__(self):
        return "Verb({})".format(", ".join(map(repr, self.words)))

class Parser:
    class ParseError(Exception):
        pass
    
    def __init__(self, verbs):
        self.verbs = verbs

    def parse(self, command):
        words = command.split()
        if not words:
            return None
        for v in self.verbs:
            try:
                variables = v.match(words)
                return variables
            except Parser.ParseError:
                continue
        else:
            return None


        
