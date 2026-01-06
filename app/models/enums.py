import enum

class RequirementScope(enum.Enum):
    MAJOR = "major"
    GEN_ED = "gen_ed"
    
class RuleType(enum.Enum):
    ALL = "all"
    ANY = "any"
    CHOOSE_N = "choose_n"
    CREDITS_TOTAL = "credits_total"
    
class Term(enum.Enum):
    FALL = "fall"
    SPRING = "spring"

class Degree(enum.Enum):
    BA = "BA"
    BS = "BS"
    BFA = "BFA"
    BM = "BM"
    
    @property 
    def label(self):
        return self.value
    
class SlotType(enum.Enum):
    COURSE = "course"
    BUCKET = "bucket"
    BUNDLE = "bundle"
    