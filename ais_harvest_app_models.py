from dataclasses import dataclass
from typing import Optional

@dataclass
class ProductType:
    id_prod: Optional[int]
    name: str
    variety: str
    id_tare: int
    tare_name: str
    tare_weight: float
    rate_per_kg: float
    active: bool = True

@dataclass
class Brigade:
    id_brigade: Optional[int]
    code: str
    area: str
    foreman: str
    active: bool = True

@dataclass
class Picker:
    id_picker: Optional[int]
    tab_num: int
    last_name: str
    first_name: str
    middle_name: str
    id_brigade: int
    brigade_code: str = ""
    active: bool = True

@dataclass
class HarvestRecord:
    id_rec: Optional[int]
    timestamp: str
    id_brigade: int
    id_picker: int
    id_prod: int
    gross_weight: float
    tare_count: int
    net_weight: float
    shift_status: str = "Открыта"
