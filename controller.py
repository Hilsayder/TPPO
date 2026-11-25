from datetime import datetime
from db_manager import DatabaseManager
from models import HarvestRecord

class HarvestController:
    def __init__(self, db: DatabaseManager):
        self.db = db

    @staticmethod
    def calculate_net_weight(gross: float, tare_count: int, tare_unit_weight: float) -> float:
        if gross <= 0:
            raise ValueError("Масса брутто должна быть положительным числом.")
        if tare_count < 0:
            raise ValueError("Количество тары не может быть отрицательным.")
        net = round(gross - tare_count * tare_unit_weight, 2)
        if net <= 0:
            raise ValueError(f"Расчётная масса нетто ({net} кг) должна быть больше нуля.")
        return net

    def register_harvest(self, id_brigade: int, id_picker: int, id_prod: int, gross: float, tare_count: int) -> HarvestRecord:
        products = {p.id_prod: p for p in self.db.get_products()}
        if id_prod not in products:
            raise ValueError("Указанный вид продукции не найден или неактивен.")
        pickers = {s.id_picker: s for s in self.db.get_pickers(id_brigade)}
        if id_picker not in pickers:
            raise ValueError("Сборщик не закреплён за выбранной бригадой.")
        tare_w = products[id_prod].tare_weight
        net_w = self.calculate_net_weight(gross, tare_count, tare_w)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rec = HarvestRecord(None, ts, id_brigade, id_picker, id_prod, gross, tare_count, net_w, "Открыта")
        rec.id_rec = self.db.insert_harvest(rec)
        return rec
