import streamlit as st
import pandas as pd
from db_manager import DatabaseManager
from controller import HarvestController

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

# --- ВКЛАДКА 1: ЖУРНАЛ СБОРА УРОЖАЯ ---
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

# --- ВКЛАДКА 2: СПРАВОЧНИКИ ---
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

# --- ВКЛАДКА 3: ОТЧЁТЫ ---
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
