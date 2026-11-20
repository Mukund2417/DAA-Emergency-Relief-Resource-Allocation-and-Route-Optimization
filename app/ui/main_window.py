"""Compact PySide6 desktop interface for scenarios and real algorithm runs."""
import json
import time
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QComboBox, QFileDialog, QFormLayout, QHBoxLayout, QLabel,
    QDoubleSpinBox, QLineEdit, QMainWindow, QMessageBox, QPushButton, QPlainTextEdit, QSpinBox,
    QTabWidget, QVBoxLayout, QWidget, QListWidget)
from app.database import repository
from app.services.algorithm_runner import run
from app.services.benchmark_service import measure
from app.services.comparison_service import compare


STYLE = """
QMainWindow, QWidget { background: #F5F6F3; color: #202722; font-family: Inter, Segoe UI, sans-serif; font-size: 10pt; }
QTabWidget::pane { border: 1px solid #E2E7E2; background: white; }
QTabBar::tab { background: #EBEFEB; padding: 10px 16px; margin-right: 3px; }
QTabBar::tab:selected { background: #26734D; color: white; }
QPushButton { background: #26734D; color: white; padding: 8px 14px; border: 0; border-radius: 4px; }
QPushButton:hover { background: #1D5D3D; }
QLineEdit, QPlainTextEdit, QComboBox, QSpinBox, QListWidget { background: white; border: 1px solid #D5DDD6; padding: 7px; }
QLabel#heading { font-size: 18pt; font-weight: 600; }
"""


class MainWindow(QMainWindow):
    algorithms = ["Fractional Knapsack", "0/1 Knapsack", "0/1 Knapsack (brute force)",
                  "Merge Sort", "Insertion Sort baseline", "Dijkstra", "Bellman-Ford",
                  "TSP Branch and Bound", "TSP exhaustive"]
    examples = {
        "Fractional Knapsack": {"capacity": 50, "items": [{"name":"Water", "weight":10, "value":60}, {"name":"Food", "weight":20, "value":100}, {"name":"Medical kit", "weight":30, "value":120}]},
        "0/1 Knapsack": {"capacity": 50, "items": [["Water",10,60],["Food",20,100],["Medical kit",30,120]]},
        "0/1 Knapsack (brute force)": {"capacity": 50, "items": [["Water",10,60],["Food",20,100],["Medical kit",30,120]]},
        "Merge Sort": {"values": [12, 4, 19, 3, 8, 8, -2]},
        "Insertion Sort baseline": {"values": [12, 4, 19, 3, 8, 8, -2]},
        "Dijkstra": {"graph": {"Depot": [["North",4], ["South",2]], "North": [["Depot",4], ["South",1], ["Clinic",5]], "South": [["Depot",2], ["North",1], ["Clinic",8]], "Clinic": [["North",5], ["South",8]]}, "source":"Depot", "target":"Clinic"},
        "Bellman-Ford": {"vertices":["Depot","North","South","Clinic"], "edges":[["Depot","North",4],["Depot","South",2],["North","South",1],["North","Clinic",5],["South","Clinic",8]], "source":"Depot"},
        "TSP Branch and Bound": {"matrix":[[None,10,15,20],[10,None,35,25],[15,35,None,30],[20,25,30,None]], "start":0},
        "TSP exhaustive": {"matrix":[[None,10,15,20],[10,None,35,25],[15,35,None,30],[20,25,30,None]], "start":0},
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Emergency Relief | DAA Workbench")
        self.resize(1120, 760)
        self.setStyleSheet(STYLE)
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self._build_dashboard()
        self._build_scenarios()
        self._build_resources()
        self._build_lab()
        self._build_reports()

    def _heading(self, title, sub):
        box = QVBoxLayout(); heading = QLabel(title); heading.setObjectName("heading")
        box.addWidget(heading); box.addWidget(QLabel(sub)); return box

    def _build_dashboard(self):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(28,24,28,24)
        layout.addLayout(self._heading("Emergency relief planning", "Academic decision-support workbench · manually entered or labelled sample data"))
        counts = repository.dashboard_counts()
        row = QHBoxLayout(); self.dashboard_cards={}
        for title, key in [("Saved scenarios","scenarios"),("Affected locations","locations"),("Inventory items","inventory"),("Saved experiments","experiments")]:
            card = QLabel(f"{title}\n{counts[key]}"); card.setStyleSheet("background:white;border:1px solid #E2E7E2;padding:20px;font-size:13pt")
            row.addWidget(card); self.dashboard_cards[key]=(title,card)
        layout.addLayout(row); layout.addSpacing(14)
        layout.addWidget(QLabel("Recent saved scenarios"))
        self.scenario_list = QListWidget(); layout.addWidget(self.scenario_list)
        layout.addWidget(QLabel("No live dispatch data is connected. Distances are user-supplied and do not imply travel time."))
        self.tabs.addTab(page, "Overview")
        self.refresh_scenarios()

    def _build_scenarios(self):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(28,24,28,24)
        layout.addLayout(self._heading("Disaster scenarios", "Create and reopen synthetic or manually entered planning cases."))
        form = QFormLayout(); self.scenario_name = QLineEdit(); self.disaster_type = QComboBox(); self.disaster_type.addItems(["Flood","Earthquake","Cyclone","Wildfire","Other"])
        self.scenario_notes = QLineEdit(); form.addRow("Scenario name",self.scenario_name); form.addRow("Disaster type",self.disaster_type); form.addRow("Notes",self.scenario_notes)
        layout.addLayout(form)
        create = QPushButton("Save scenario"); create.clicked.connect(self.create_scenario); layout.addWidget(create)
        self.scenario_table = QListWidget(); layout.addWidget(self.scenario_table)
        self.location_scenario = QComboBox(); self.location_name = QLineEdit(); self.location_priority = QSpinBox(); self.location_priority.setRange(1,5); self.location_priority.setValue(3)
        location_form = QFormLayout(); location_form.addRow("Scenario",self.location_scenario); location_form.addRow("Affected location",self.location_name); location_form.addRow("Priority (1-5)",self.location_priority)
        layout.addWidget(QLabel("Add an affected location")); layout.addLayout(location_form)
        add_location_button = QPushButton("Save location"); add_location_button.clicked.connect(self.add_location); layout.addWidget(add_location_button)
        self.tabs.addTab(page,"Scenarios")
        self.refresh_scenarios()

    def _build_lab(self):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(28,24,28,24)
        layout.addLayout(self._heading("Algorithm lab", "Edit the JSON input, run an independently implemented algorithm, and save the actual result."))
        self.algorithm = QComboBox(); self.algorithm.addItems(self.algorithms); self.algorithm.currentTextChanged.connect(self.load_example)
        layout.addWidget(QLabel("Algorithm")); layout.addWidget(self.algorithm)
        self.input = QPlainTextEdit(); self.input.setMinimumHeight(220); layout.addWidget(QLabel("Input configuration (JSON)")); layout.addWidget(self.input)
        buttons = QHBoxLayout(); run_button = QPushButton("Run algorithm"); run_button.clicked.connect(self.run_algorithm)
        bench_button = QPushButton("Measure 5 runs"); bench_button.clicked.connect(self.run_benchmark)
        buttons.addWidget(run_button); buttons.addWidget(bench_button); layout.addLayout(buttons)
        self.result = QPlainTextEdit(); self.result.setReadOnly(True); self.result.setMinimumHeight(220)
        layout.addWidget(QLabel("Actual output and execution details")); layout.addWidget(self.result)
        compare_row=QHBoxLayout(); self.comparison=QComboBox(); self.comparison.addItems(["0/1 Knapsack","Shortest paths","TSP","Sorting"])
        self.comparison.currentTextChanged.connect(self.load_comparison_example)
        compare_button=QPushButton("Compare equivalent algorithms"); compare_button.clicked.connect(self.run_comparison)
        compare_row.addWidget(self.comparison); compare_row.addWidget(compare_button); layout.addLayout(compare_row)
        self.load_comparison_example(self.comparison.currentText())
        self.tabs.addTab(page,"Algorithm lab")
        self.load_example(self.algorithm.currentText())

    def _build_resources(self):
        page=QWidget(); layout=QVBoxLayout(page); layout.setContentsMargins(28,24,28,24)
        layout.addLayout(self._heading("Resource inventory", "Store locally available supplies. Allocation experiments use explicitly entered algorithm inputs."))
        form=QFormLayout(); self.item_name=QLineEdit(); self.item_category=QComboBox(); self.item_category.setEditable(True)
        self.item_category.addItems(["Water","Food","Medical","Shelter","Other"])
        self.item_weight=QDoubleSpinBox(); self.item_weight.setRange(0.001,1000000); self.item_weight.setValue(1); self.item_weight.setSuffix(" kg/unit")
        self.item_quantity=QDoubleSpinBox(); self.item_quantity.setRange(0,1000000); self.item_quantity.setValue(1)
        self.item_value=QDoubleSpinBox(); self.item_value.setRange(0,1000000); self.item_value.setValue(1)
        form.addRow("Item name",self.item_name); form.addRow("Category",self.item_category); form.addRow("Weight per unit",self.item_weight); form.addRow("Available quantity",self.item_quantity); form.addRow("Priority/value per unit",self.item_value)
        layout.addLayout(form); save=QPushButton("Save inventory item"); save.clicked.connect(self.add_inventory_item); layout.addWidget(save)
        self.inventory_list=QListWidget(); layout.addWidget(self.inventory_list); self.refresh_inventory()
        self.tabs.addTab(page,"Resources")

    def _build_reports(self):
        page=QWidget(); layout=QVBoxLayout(page); layout.setContentsMargins(28,24,28,24)
        layout.addLayout(self._heading("Experiments and reports", "Saved algorithm runs and benchmark measurements from this local database."))
        refresh=QPushButton("Refresh saved results"); refresh.clicked.connect(self.refresh_reports); layout.addWidget(refresh)
        self.report_list=QListWidget(); layout.addWidget(self.report_list)
        export=QPushButton("Export this summary as Markdown"); export.clicked.connect(self.export_report); layout.addWidget(export)
        self.tabs.addTab(page,"Reports")
        self.refresh_reports()

    def refresh_scenarios(self):
        scenarios = repository.list_scenarios()
        for widget in (getattr(self,"scenario_list",None), getattr(self,"scenario_table",None)):
            if widget:
                widget.clear()
                for row in scenarios: widget.addItem(f"{row['name']} · {row['disaster_type']} · {row['location_count']} locations · {row['created_at']}")
        if hasattr(self,"location_scenario"):
            self.location_scenario.clear()
            for row in scenarios: self.location_scenario.addItem(row["name"],row["id"])
        self.refresh_dashboard()

    def refresh_dashboard(self):
        if not hasattr(self,"dashboard_cards"): return
        counts=repository.dashboard_counts()
        for key,(title,card) in self.dashboard_cards.items():
            card.setText(f"{title}\n{counts[key]}")

    def refresh_inventory(self):
        if not hasattr(self,"inventory_list"): return
        self.inventory_list.clear()
        items=repository.list_inventory()
        for item in items: self.inventory_list.addItem(f"{item['name']} · {item['category']} · {item['quantity']:g} units · {item['weight']:g} kg/unit · value {item['value']:g}")
        if not items: self.inventory_list.addItem("No inventory recorded yet.")
        self.refresh_dashboard()

    def add_inventory_item(self):
        try:
            repository.add_inventory_item(self.item_name.text(),self.item_category.currentText(),self.item_weight.value(),self.item_quantity.value(),self.item_value.value())
            self.item_name.clear(); self.refresh_inventory()
            QMessageBox.information(self,"Saved","Inventory item added to the local database.")
        except Exception as exc: QMessageBox.warning(self,"Could not save",str(exc))

    def create_scenario(self):
        try:
            repository.create_scenario(self.scenario_name.text(),self.disaster_type.currentText(),self.scenario_notes.text())
            self.scenario_name.clear(); self.scenario_notes.clear(); self.refresh_scenarios()
            QMessageBox.information(self,"Saved","Scenario saved in the local SQLite database.")
        except Exception as exc: QMessageBox.warning(self,"Could not save",str(exc))

    def add_location(self):
        try:
            scenario_id=self.location_scenario.currentData()
            if scenario_id is None: raise ValueError("Create a scenario first")
            repository.add_location(scenario_id,self.location_name.text(),self.location_priority.value())
            self.location_name.clear(); self.refresh_scenarios()
            QMessageBox.information(self,"Saved","Affected location added to the scenario.")
        except Exception as exc: QMessageBox.warning(self,"Could not save",str(exc))

    def load_example(self, name):
        if hasattr(self,"input"): self.input.setPlainText(json.dumps(self.examples[name],indent=2))

    def _execute(self):
        name = self.algorithm.currentText(); data = json.loads(self.input.toPlainText())
        start = time.perf_counter(); output = run(name,data); elapsed = time.perf_counter()-start
        return name,data,output,elapsed

    def run_algorithm(self):
        try:
            name,data,output,elapsed = self._execute()
            operations = int(output.get("operations",output.get("expanded",0)))
            repository.save_experiment(name,name,data,output,elapsed,operations)
            self.result.setPlainText(json.dumps({"output":output,"measured_seconds":elapsed,"operation_count":operations},indent=2,default=str))
            self.refresh_dashboard(); self.refresh_reports()
        except Exception as exc: QMessageBox.warning(self,"Algorithm input or execution error",str(exc))

    def run_benchmark(self):
        try:
            name,data,_,_ = self._execute()
            result = measure(lambda:run(name,data),5)
            ops=int(result["result"].get("operations",result["result"].get("expanded",0)))
            repository.add_benchmark(name,len(data.get("items",data.get("values",data.get("graph",data.get("matrix",[]))))),
                "manual/sample input",result["repeats"],result["median_seconds"],ops)
            self.result.setPlainText(json.dumps({"result":result["result"],"median_seconds":result["median_seconds"],
                "min_seconds":result["min_seconds"],"max_seconds":result["max_seconds"],"repeats":result["repeats"],
                "note":"Measured on this computer; this is not a theoretical complexity bound."},indent=2,default=str))
        except Exception as exc: QMessageBox.warning(self,"Benchmark error",str(exc))

    def run_comparison(self):
        try:
            result=compare(self.comparison.currentText(),json.loads(self.input.toPlainText()))
            self.result.setPlainText(json.dumps(result,indent=2,default=str))
        except Exception as exc: QMessageBox.warning(self,"Comparison error",str(exc))

    def load_comparison_example(self, category):
        pair={"0/1 Knapsack":"0/1 Knapsack","Shortest paths":"Dijkstra","TSP":"TSP Branch and Bound","Sorting":"Merge Sort"}
        if hasattr(self,"input"):
            selected=pair[category]
            self.algorithm.setCurrentText(selected)
            self.input.setPlainText(json.dumps(self.examples[selected],indent=2))

    def refresh_reports(self):
        if not hasattr(self,"report_list"): return
        self.report_list.clear()
        experiments=repository.recent_experiments()
        benchmarks=repository.recent_benchmarks()
        for row in experiments:
            self.report_list.addItem(f"Run #{row['id']} · {row['algorithm']} · {row['elapsed_seconds']:.6f}s · {row['operation_count']} operations · {row['created_at']}")
        for row in benchmarks:
            self.report_list.addItem(f"Benchmark · {row['algorithm']} · n={row['input_size']} · median {row['elapsed_seconds']:.6f}s ({row['repeat_count']} runs) · {row['created_at']}")
        if not experiments and not benchmarks: self.report_list.addItem("No saved runs yet. Run an algorithm or benchmark in Algorithm lab.")

    def export_report(self):
        path,_=QFileDialog.getSaveFileName(self,"Export experiment summary","experiment-summary.md","Markdown (*.md)")
        if not path: return
        experiments=repository.recent_experiments(); benchmarks=repository.recent_benchmarks()
        lines=["# Emergency Relief DAA Experiment Summary","", "Generated from actual local SQLite records.", "", "## Algorithm runs", ""]
        lines += [f"- {r['created_at']} — {r['algorithm']}: {r['elapsed_seconds']:.8f}s, {r['operation_count']} operations" for r in experiments] or ["- No saved runs."]
        lines += ["", "## Benchmarks", ""]
        lines += [f"- {r['created_at']} — {r['algorithm']} (n={r['input_size']}, {r['repeat_count']} repeats): {r['elapsed_seconds']:.8f}s median, {r['operation_count']} operations" for r in benchmarks] or ["- No saved benchmarks."]
        lines += ["", "Measurements depend on the computer and input. They are not theoretical complexity bounds."]
        try:
            with open(path,"w",encoding="utf-8") as stream: stream.write("\n".join(lines))
            QMessageBox.information(self,"Exported","Experiment summary saved.")
        except OSError as exc: QMessageBox.warning(self,"Export failed",str(exc))


def launch() -> int:
    app = QApplication.instance() or QApplication([])
    window = MainWindow(); window.show()
    return app.exec()
