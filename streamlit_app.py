import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple
import pandas as pd
import streamlit as st


# ==============================================================================
# 1. МОДЕЛИ ПРЕДМЕТНОЙ ОБЛАСТИ
# ==============================================================================
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


# ==============================================================================
# 2. СЛОЙ ДОСТУПА К БАЗЕ ДАННЫХ (SQLite 3, 3НФ)
# ==============================================================================
class DatabaseManager:
    def __init__(self, db_path: str = "harvest_kruglov.db"):
        self.db_path = db_path
        self._init_schema()

    def _connect(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
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


# ==============================================================================
# 3. КОНТРОЛЛЕР БИЗНЕС-ЛОГИКИ
# ==============================================================================
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


# ==============================================================================
# 4. ВЕБ-ИНТЕРФЕЙС STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="АИС «Учёт урожая» — ООО «Круглов»",
    page_icon="🌾",
    layout="wide"
)

@st.cache_resource
def init_system():
    db = DatabaseManager("harvest_kruglov.db")
    db.seed_demo_data()
    ctrl = HarvestController(db)
    return db, ctrl

db, ctrl = init_system()

st.title("🌾 АИС «Учёт урожая» — ООО «Круглов» (г. Краснодар)")
st.caption("Оперативный учёт сбора урожая, ведение справочников НСИ и расчёт сдельной выработки")

tab_journal, tab_refs, tab_reports = st.tabs([
    "📋 Журнал учёта сбора урожая",
    "🗂️ Справочники (Продукция, Бригады, Сборщики)",
    "📊 Ведомости выработки и отчёты"
])

with tab_journal:
    st.subheader("Регистрация новой сдачи продукции")

    brigades = db.get_brigades()
    products = db.get_products()

    brigade_map = {f"{b.code} ({b.area})": b for b in brigades}
    product_map = {f"{p.name} — {p.variety} (тара: {p.tare_weight} кг)": p for p in products}

    col1, col2, col3 = st.columns(3)
    with col1:
        sel_brigade_label = st.selectbox("Бригада", list(brigade_map.keys()))
        sel_brigade = brigade_map[sel_brigade_label]
    with col2:
        pickers = db.get_pickers(sel_brigade.id_brigade)
        picker_map = {f"{s.tab_num} — {s.last_name} {s.first_name}": s for s in pickers}
        sel_picker_label = st.selectbox("Сборщик", list(picker_map.keys()))
        sel_picker = picker_map[sel_picker_label]
    with col3:
        sel_prod_label = st.selectbox("Вид продукции", list(product_map.keys()))
        sel_prod = product_map[sel_prod_label]

    col4, col5, col6, col7 = st.columns([1, 1, 1, 1.2])
    with col4:
        gross_weight = st.number_input("Масса брутто, кг", min_value=0.1, value=35.0, step=0.5)
    with col5:
        tare_count = st.number_input("Количество тары, шт.", min_value=0, value=2, step=1)
    with col6:
        preview_net = round(gross_weight - tare_count * sel_prod.tare_weight, 2)
        st.metric("Масса нетто (авто)", f"{preview_net:.2f} кг")
    with col7:
        st.write("")
        st.write("")
        if st.button("➕ Записать в журнал", type="primary", use_container_width=True):
            try:
                rec = ctrl.register_harvest(
                    sel_brigade.id_brigade,
                    sel_picker.id_picker,
                    sel_prod.id_prod,
                    gross_weight,
                    tare_count
                )
                st.success(f"Запись №{rec.id_rec} сохранена! Масса нетто: {rec.net_weight:.2f} кг.")
            except Exception as e:
                st.error(f"Ошибка валидации: {e}")

    st.divider()
    st.subheader("Текущий журнал сбора урожая за смену")
    journal_rows = db.get_journal()
    df_journal = pd.DataFrame(
        journal_rows,
        columns=["№", "Дата и время", "Бригада", "Сборщик", "Вид продукции", "Брутто, кг", "Тара, шт.", "Нетто, кг", "Статус"]
    )
    st.dataframe(df_journal, use_container_width=True, hide_index=True)

with tab_refs:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Список видов продукции")
        df_prod = pd.DataFrame([
            {
                "ID": p.id_prod,
                "Культура": p.name,
                "Сорт": p.variety,
                "Тара": p.tare_name,
                "Вес тары, кг": p.tare_weight,
                "Расценка, руб./кг": p.rate_per_kg
            } for p in products
        ])
        st.dataframe(df_prod, use_container_width=True, hide_index=True)

        st.subheader("Список бригад")
        df_brig = pd.DataFrame([
            {
                "ID": b.id_brigade,
                "Шифр": b.code,
                "Участок уборки": b.area,
                "Бригадир": b.foreman
            } for b in brigades
        ])
        st.dataframe(df_brig, use_container_width=True, hide_index=True)

    with c2:
        st.subheader("Список сборщиков")
        all_pickers = db.get_pickers()
        df_pick = pd.DataFrame([
            {
                "Таб. №": s.tab_num,
                "Фамилия": s.last_name,
                "Имя": s.first_name,
                "Отчество": s.middle_name,
                "Бригада": s.brigade_code
            } for s in all_pickers
        ])
        st.dataframe(df_pick, use_container_width=True, hide_index=True)

with tab_reports:
    st.subheader("Сводная ведомость сдельной выработки сборщиков")
    rep_rows = db.get_salary_report()
    df_rep = pd.DataFrame(
        rep_rows,
        columns=["Таб. №", "ФИО сборщика", "Бригада", "Кол-во сдач", "Итого нетто, кг", "Начислено, руб."]
    )
    st.dataframe(df_rep, use_container_width=True, hide_index=True)

    m1, m2, m3 = st.columns(3)
    m1.metric("Всего сдач за смену", int(df_rep["Кол-во сдач"].sum()))
    m2.metric("Валовой сбор нетто", f"{df_rep['Итого нетто, кг'].sum():.2f} кг")
    m3.metric("Фонд сдельной оплаты", f"{df_rep['Начислено, руб.'].sum():.2f} руб.")

    csv_data = df_rep.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 Скачать ведомость (CSV для Excel)",
        data=csv_data,
        file_name="vedomost_kruglov.csv",
        mime="text/csv"
    )
