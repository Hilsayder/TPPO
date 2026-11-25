import tkinter as tk
from tkinter import ttk, messagebox
from db_manager import DatabaseManager
from controller import HarvestController

class HarvestApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("АИС «Учёт урожая» — ООО «Круглов» (г. Краснодар)")
        self.geometry("1040x640")
        self.db = DatabaseManager()
        self.db.seed_demo_data()
        self.ctrl = HarvestController(self.db)
        self._build_ui()

    def _build_ui(self):
        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.tab_journal = ttk.Frame(nb)
        self.tab_refs = ttk.Frame(nb)
        self.tab_reports = ttk.Frame(nb)
        nb.add(self.tab_journal, text="Журнал учёта сбора урожая")
        nb.add(self.tab_refs, text="Справочники (Продукция, Бригады, Сборщики)")
        nb.add(self.tab_reports, text="Ведомости выработки и отчёты")
        self._init_journal_tab()
        self._init_reports_tab()

    def _init_journal_tab(self):
        frm = ttk.LabelFrame(self.tab_journal, text="Регистрация сдачи продукции")
        frm.pack(fill=tk.X, padx=6, pady=6)
        ttk.Label(frm, text="Бригада:").grid(row=0, column=0, padx=5, pady=5)
        self.cb_brigade = ttk.Combobox(frm, width=18, state="readonly")
        self.cb_brigade.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(frm, text="Сборщик:").grid(row=0, column=2, padx=5, pady=5)
        self.cb_picker = ttk.Combobox(frm, width=24, state="readonly")
        self.cb_picker.grid(row=0, column=3, padx=5, pady=5)
        ttk.Label(frm, text="Вид продукции:").grid(row=0, column=4, padx=5, pady=5)
        self.cb_prod = ttk.Combobox(frm, width=22, state="readonly")
        self.cb_prod.grid(row=0, column=5, padx=5, pady=5)
        ttk.Label(frm, text="Брутто (кг):").grid(row=1, column=0, padx=5, pady=5)
        self.ent_gross = ttk.Entry(frm, width=14)
        self.ent_gross.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(frm, text="Кол-во тары:").grid(row=1, column=2, padx=5, pady=5)
        self.ent_tare = ttk.Entry(frm, width=10)
        self.ent_tare.grid(row=1, column=3, padx=5, pady=5)
        btn = ttk.Button(frm, text="Записать в журнал", command=self._on_save)
        btn.grid(row=1, column=5, padx=5, pady=5)

    def _init_reports_tab(self):
        cols = ("Таб. №", "ФИО сборщика", "Бригада", "Сдач", "Итого нетто, кг", "Начислено, руб.")
        self.tree_rep = ttk.Treeview(self.tab_reports, columns=cols, show="headings")
        for c in cols:
            self.tree_rep.heading(c, text=c)
        self.tree_rep.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

    def _on_save(self):
        try:
            gross = float(self.ent_gross.get())
            tare = int(self.ent_tare.get())
            self.ctrl.register_harvest(1, 1, 1, gross, tare)
            messagebox.showinfo("Успех", "Запись сохранена в журнал.")
        except Exception as exc:
            messagebox.showerror("Ошибка ввода", str(exc))

if __name__ == "__main__":
    app = HarvestApp()
    app.mainloop()
