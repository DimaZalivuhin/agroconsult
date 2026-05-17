"""Domain enums shared across models and schemas."""
from enum import Enum


class UserRole(str, Enum):
    """Roles within the system."""

    FARMER = "farmer"
    ADMIN = "admin"


class FarmType(str, Enum):
    """Legal form of the farm operation."""

    KFH = "kfh"          # Крестьянское (фермерское) хозяйство
    LPH = "lph"          # Личное подсобное хозяйство
    IP = "ip"            # ИП — глава КФХ или иной с/х ИП
    OOO = "ooo"          # Сельхозпредприятие в форме юрлица
    COOP = "coop"        # Сельскохозяйственный потребительский кооператив
    OTHER = "other"


class FarmDirection(str, Enum):
    """Main production direction of the farm."""

    CROP = "crop"             # Растениеводство
    LIVESTOCK = "livestock"   # Животноводство
    DAIRY = "dairy"           # Молочное скотоводство
    MEAT = "meat"             # Мясное скотоводство
    POULTRY = "poultry"       # Птицеводство
    BEEKEEPING = "beekeeping" # Пчеловодство
    AQUACULTURE = "aquaculture"  # Аквакультура
    MIXED = "mixed"
    OTHER = "other"


class FarmerStatus(str, Enum):
    """Lifecycle status used to filter measures relevant to the user."""

    BEGINNING = "beginning"   # Начинающий фермер
    OPERATING = "operating"   # Действующий
    EXPANDING = "expanding"   # Расширяющий деятельность


class DocumentType(str, Enum):
    """Type of legal document."""

    FEDERAL_LAW = "federal_law"
    GOVERNMENT_DECREE = "government_decree"
    MINISTRY_ORDER = "ministry_order"
    REGIONAL_ACT = "regional_act"
    TAX_CODE = "tax_code"
    METHODOLOGY = "methodology"
    OTHER = "other"


class DocumentStatus(str, Enum):
    """Indexing lifecycle of a document in the knowledge base."""

    PENDING = "pending"
    PARSING = "parsing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    INDEXED = "indexed"
    FAILED = "failed"
    ARCHIVED = "archived"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class FeedbackKind(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    HALLUCINATION = "hallucination"
    OUTDATED = "outdated"
