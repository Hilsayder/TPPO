import sqlite3
from typing import List, Tuple, Optional
from models import ProductType, Brigade, Picker, HarvestRecord

class DatabaseManager:
    def __init__(self, db_path: str = "harvest_kruglov.db"):
        self.db_path = db_path
        self._init_schema()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_schema(self):
        with self._connect() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS Типы_тары (
                id_тары INTEGER PRIMARY KEY AUTOINCREMENT,
                наименование VARCHAR(50) NOT NULL UNIQUE,
                масса_единицы DECIMAL(6,2) NOT NULL CHECK (масса_единицы >= 0)
            );
            CREATE TABLE IF NOT EXISTS Виды_продукции (
                id_продукции INTEGER PRIMARY KEY AUTOINCREMENT,
                наименование VARCHAR(80) NOT NULL,
                сорт VARCHAR(50) NOT NULL,
                id_тары INTEGER NOT NULL,
                расценка_кг DECIMAL(10,2) NOT NULL CHECK (расценка_кг > 0),
                активен BOOLEAN NOT NULL DEFAULT 1,
                FOREIGN KEY (id_тары) REFERENCES Типы_тары(id_тары) ON DELETE RESTRICT
            );
            CREATE TABLE IF NOT EXISTS Бригады (
                id_бригады INTEGER PRIMARY KEY AUTOINCREMENT,
                номер_бригады VARCHAR(20) NOT NULL UNIQUE,
                участок_работы VARCHAR(100) NOT NULL,
                фио_бригадира VARCHAR(120) NOT NULL,
                активна BOOLEAN NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS Сборщики (
                id_сборщика INTEGER PRIMARY KEY AUTOINCREMENT,
                табельный_номер INTEGER NOT NULL UNIQUE,
                фамилия VARCHAR(50) NOT NULL,
                имя VARCHAR(50) NOT NULL,
                отчество VARCHAR(50),
                id_бригады INTEGER NOT NULL,
                активен BOOLEAN NOT NULL DEFAULT 1,
                FOREIGN KEY (id_бригады) REFERENCES Бригады(id_бригады) ON DELETE RESTRICT
            );
            CREATE TABLE IF NOT EXISTS Журнал_сбора_урожая (
                id_записи INTEGER PRIMARY KEY AUTOINCREMENT,
                дата_время TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                id_бригады INTEGER NOT NULL,
                id_сборщика INTEGER NOT NULL,
                id_продукции INTEGER NOT NULL,
                масса_брутто DECIMAL(8,2) NOT NULL CHECK (масса_брутто > 0),
                колво_тары INTEGER NOT NULL CHECK (колво_тары >= 0),
                масса_нетто DECIMAL(8,2) NOT NULL CHECK (масса_нетто > 0),
                статус_смены VARCHAR(20) NOT NULL DEFAULT 'Открыта',
                FOREIGN KEY (id_бригады) REFERENCES Бригады(id_бригады) ON DELETE RESTRICT,
                FOREIGN KEY (id_сборщика) REFERENCES Сборщики(id_сборщика) ON DELETE RESTRICT,
                FOREIGN KEY (id_продукции) REFERENCES Виды_продукции(id_продукции) ON DELETE RESTRICT
            );
            CREATE TABLE IF NOT EXISTS Журнал_аудита (
                id_лога INTEGER PRIMARY KEY AUTOINCREMENT,
                id_записи INTEGER NOT NULL,
                старое_нетто DECIMAL(8,2) NOT NULL,
                новое_нетто DECIMAL(8,2) NOT NULL,
                причина VARCHAR(200) NOT NULL,
                время_правки TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_записи) REFERENCES Журнал_сбора_урожая(id_записи) ON DELETE RESTRICT
            );
            """)

    def seed_demo_data(self):
        with self._connect() as conn:
            cur = conn.cursor()
            if cur.execute("SELECT COUNT(*) FROM Типы_тары").fetchone()[0] > 0:
                return
            cur.executescript("""
            INSERT INTO Типы_тары (наименование, масса_единицы) VALUES
                ('Ящик пластиковый 15 кг', 1.20),
                ('Ведро эмалированное 10 л', 0.85),
                ('Лоток ягодный 5 кг', 0.35);
            INSERT INTO Виды_продукции (наименование, сорт, id_тары, расценка_кг) VALUES
                ('Яблоко', 'Айдаред (1 сорт)', 1, 14.50),
                ('Черешня', 'Валерий Чкалов', 3, 45.00),
                ('Клубника', 'Альбион', 3, 55.00),
                ('Томат грунтовой', 'Сливка', 1, 12.00);
            INSERT INTO Бригады (номер_бригады, участок_работы, фио_бригадира) VALUES
                ('БР-01', 'Сад №1 (квартал А)', 'Петренко Сергей Иванович'),
                ('БР-02', 'Ягодник №3', 'Ковалёва Елена Викторовна'),
                ('БР-03', 'Овощное поле №2', 'Гончаров Виктор Павлович');
            INSERT INTO Сборщики (табельный_номер, фамилия, имя, отчество, id_бригады) VALUES
                (101, 'Сидоров', 'Алексей', 'Петрович', 1),
                (102, 'Мельник', 'Ольга', 'Николаевна', 1),
                (103, 'Ткаченко', 'Дмитрий', 'Александрович', 2),
                (104, 'Бондаренко', 'Ирина', 'Сергеевна', 2),
                (105, 'Кравцов', 'Николай', 'Игоревич', 3);
            INSERT INTO Журнал_сбора_урожая (дата_время, id_бригады, id_сборщика, id_продукции, масса_брутто, колво_тары, масса_нетто) VALUES
                ('2026-07-15 08:45:12', 1, 1, 1, 32.40, 2, 30.00),
                ('2026-07-15 09:30:05', 1, 2, 1, 47.60, 3, 44.00),
                ('2026-07-15 10:15:40', 2, 3, 2, 11.05, 3, 10.00),
                ('2026-07-15 11:05:18', 2, 4, 3, 16.40, 4, 15.00),
                ('2026-07-15 11:50:33', 3, 5, 4, 62.40, 2, 60.00);
            """)

    def get_products(self) -> List[ProductType]:
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT p.id_продукции, p.наименование, p.сорт, p.id_тары, t.наименование, t.масса_единицы, p.расценка_кг, p.активен
                FROM Виды_продукции p JOIN Типы_тары t ON p.id_тары = t.id_тары
                WHERE p.активен = 1 ORDER BY p.id_продукции
            """).fetchall()
            return [ProductType(*r) for r in rows]

    def get_brigades(self) -> List[Brigade]:
        with self._connect() as conn:
            rows = conn.execute("SELECT id_бригады, номер_бригады, участок_работы, фио_бригадира, активна FROM Бригады WHERE активна = 1").fetchall()
            return [Brigade(*r) for r in rows]

    def get_pickers(self, id_brigade: Optional[int] = None) -> List[Picker]:
        with self._connect() as conn:
            if id_brigade:
                rows = conn.execute("""
                    SELECT s.id_сборщика, s.табельный_номер, s.фамилия, s.имя, s.отчество, s.id_бригады, b.номер_бригады, s.активен
                    FROM Сборщики s JOIN Бригады b ON s.id_бригады = b.id_бригады
                    WHERE s.активен = 1 AND s.id_бригады = ?
                """, (id_brigade,)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT s.id_сборщика, s.табельный_номер, s.фамилия, s.имя, s.отчество, s.id_бригады, b.номер_бригады, s.активен
                    FROM Сборщики s JOIN Бригады b ON s.id_бригады = b.id_бригады
                    WHERE s.активен = 1 ORDER BY s.табельный_номер
                """).fetchall()
            return [Picker(*r) for r in rows]

    def insert_harvest(self, rec: HarvestRecord) -> int:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO Журнал_сбора_урожая (дата_время, id_бригады, id_сборщика, id_продукции, масса_брутто, колво_тары, масса_нетто, статус_смены)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (rec.timestamp, rec.id_brigade, rec.id_picker, rec.id_prod, rec.gross_weight, rec.tare_count, rec.net_weight, rec.shift_status))
            return cur.lastrowid

    def get_journal(self) -> List[Tuple]:
        with self._connect() as conn:
            return conn.execute("""
                SELECT j.id_записи, j.дата_время, b.номер_бригады,
                       s.фамилия || ' ' || substr(s.имя,1,1) || '.' || substr(COALESCE(s.отчество,''),1,1) || '.',
                       p.наименование || ' (' || p.сорт || ')',
                       j.масса_брутто, j.колво_тары, j.масса_нетто, j.статус_смены
                FROM Журнал_сбора_урожая j
                JOIN Бригады b ON j.id_бригады = b.id_бригады
                JOIN Сборщики s ON j.id_сборщика = s.id_сборщика
                JOIN Виды_продукции p ON j.id_продукции = p.id_продукции
                ORDER BY j.id_записи DESC
            """).fetchall()

    def get_salary_report(self) -> List[Tuple]:
        with self._connect() as conn:
            return conn.execute("""
                SELECT s.табельный_номер,
                       s.фамилия || ' ' || s.имя || ' ' || COALESCE(s.отчество,''),
                       b.номер_бригады,
                       COUNT(j.id_записи) AS сдач,
                       ROUND(SUM(j.масса_нетто), 2) AS итого_кг,
                       ROUND(SUM(j.масса_нетто * p.расценка_кг), 2) AS начислено_руб
                FROM Журнал_сбора_урожая j
                JOIN Сборщики s ON j.id_сборщика = s.id_сборщика
                JOIN Бригады b ON j.id_бригады = b.id_бригады
                JOIN Виды_продукции p ON j.id_продукции = p.id_продукции
                GROUP BY s.id_сборщика
                ORDER BY начислено_руб DESC
            """).fetchall()
