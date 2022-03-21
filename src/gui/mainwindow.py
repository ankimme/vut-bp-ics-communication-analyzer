"""This file contains code of the main window of the application.

Author
------
Andrea Chimenti

Date
----
March 2022
"""

from bidict import bidict
import pandas as pd

from PyQt6.QtWidgets import QMainWindow, QApplication, QToolBar, QFileDialog, QTabWidget, QMessageBox
from PyQt6.QtGui import QIcon, QAction

from dsmanipulator import dsloader as dsl
from dsmanipulator import dscreator as dsc
from gui.components import OpenCsvWizard
from gui.tabs import OriginalDfTab, StatsTab, PairPlotsTab
from gui.utils import EventType, EventHandler, EventData
from gui.components import SelectMasterStationsDialog, SelectSlavesDialog
from dsmanipulator.utils import Direction, Station

# from .datamodels import DataFrameModel


MASTER_STATION_PORT = 2404


class MainWindow(QMainWindow):
    """Main application window.

    Attributes
    ----------
    actions : dict[str, QAction]
        Actions used in menu and toolbar.
    df : pd.DataFrame
        Original dataframe loaded from csv.
    event_handler : EventHandler
        A simple event handler for events that should change data in UI.
    self.original_cols : list[str]
        Columns that where part of the original csv file.
    self.file_path : str
        File path of the csv file.
    self.master_station_id : int
        ID of station that should be treated as master.
    self.slave_stations : list[int]
        IDs of stations that should be treated as slaves.
    self.station_ids : bidict[int, Station]
        Key : ID of station.
        Value : Station.
    self.pair_ids : bidict[int, frozenset]
        Key : ID of station.
        Value : Pair of station ids.
        Direction does not matter.
    self.direction_ids : bidict[int, Direction]
        Key : ID of station.
        Value : Pair of station ids. Source and destination.
        Direction does matter.

    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ICS Analyzer")
        self.setMinimumSize(800, 500)

        self.actions = self.create_actions()
        self.df: pd.DataFrame = None
        self.event_handler = EventHandler()
        self.original_cols: list[str]
        self.file_path: str
        self.master_station_id: int
        self.slave_stations: list[int] = None
        self.station_ids: bidict[int, Station]
        self.pair_ids: bidict[int, frozenset]
        self.direction_ids: bidict[int, Direction]

        toolbar = self.create_toolbar()
        self.addToolBar(toolbar)

        # self.df_model: DataFrameModel
        # self.stat_widgets: dict[str, InfoLabel] = {}
        # self.fcn: FileColumnNames
        # self.master_station_id: int

        # self.init_toolbar()

        tabs = QTabWidget()

        # TAB 1 #
        original_df_tab = OriginalDfTab(self)
        self.event_handler.subscribe(EventType.DATAFRAME_CHANGED, original_df_tab.update_model)
        tabs.addTab(original_df_tab, "Original Dataframe")

        # TAB 2 #

        stats_tab = StatsTab(self)
        self.event_handler.subscribe(EventType.DATAFRAME_CHANGED, stats_tab.update_stats)
        self.event_handler.subscribe(EventType.MASTER_STATION_CHANGED, stats_tab.update_master_station)
        tabs.addTab(stats_tab, "General statistics")

        # TAB 3 #

        pair_plots_tab = PairPlotsTab(self)
        self.event_handler.subscribe(EventType.DATAFRAME_CHANGED, pair_plots_tab.update_plots)
        self.event_handler.subscribe(EventType.MASTER_STATION_CHANGED, pair_plots_tab.update_master_station)

        tabs.addTab(pair_plots_tab, "Communication pairs")

        self.setCentralWidget(tabs)

        self.event_handler.subscribe(EventType.SLAVE_STATIONS_CHANGED, lambda data: print(data.slave_stations))

    # region Actions

    def load_csv(self) -> None:
        # TODO delete test

        if True:
            self.file_path = "placeholder.py"
            import pickle

            with open("../save/fcn.pkl", "rb") as f:
                self.fcn = pickle.load(f)
            self.df = pd.read_pickle("../save/df.pkl")
            self.original_cols = self.df.columns

            self.prepare_df()

            data = self.get_event_data()
            self.event_handler.notify(EventType.DATAFRAME_CHANGED, data)

            return

        file_path, _ = QFileDialog.getOpenFileName(parent=self, caption="Open file", filter="CSV files (*.csv *.txt)")

        if file_path:
            self.file_path = file_path
            dialog = OpenCsvWizard(file_path)
            if dialog.exec():
                # TODO exception
                dialect, dtype, self.fcn = dialog.get_csv_settings()
                self.df = dsl.load_data(file_path, dtype, dialect)
                self.df.to_pickle("../save/df.pkl")  # TODO delete
                self.original_cols = self.df.columns

                self.prepare_df()

                data = self.get_event_data()
                self.event_handler.notify(EventType.DATAFRAME_CHANGED, data)

                # # TODO delete
                import pickle

                with open("../save/fcn.pkl", "wb") as f:
                    pickle.dump(self.fcn, f)

    def select_master_station(self) -> None:
        if self.df is not None:
            dlg = SelectMasterStationsDialog(self.station_ids, self.master_station_id, parent=self)
            if dlg.exec():
                self.master_station_id = dlg.get_master_station_id()

                data = self.get_event_data()
                self.event_handler.notify(EventType.MASTER_STATION_CHANGED, data)
        else:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Warning")
            dlg.setText("Pleas load a CSV file before proceeding")
            dlg.setIcon(QMessageBox.Icon.Warning)
            dlg.exec()

    def select_slaves(self) -> None:
        if self.df is not None:
            dlg = SelectSlavesDialog(self.master_station_id, self.station_ids, self.pair_ids, parent=self)
            if dlg.exec():
                self.slave_stations = dlg.get_slave_stations_ids()

                data = self.get_event_data()
                self.event_handler.notify(EventType.SLAVE_STATIONS_CHANGED, data)
        else:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Warning")
            dlg.setText("Pleas load a CSV file before proceeding")
            dlg.setIcon(QMessageBox.Icon.Warning)
            dlg.exec()

    # endregion

    # region Utilities

    def prepare_df(self) -> None:
        dsc.add_relative_days(self.df, self.fcn, inplace=True)

        self.station_ids = dsc.create_station_ids(self.df, self.fcn)
        dsc.add_station_id(self.df, self.fcn, self.station_ids, inplace=True)

        self.pair_ids = dsc.create_pair_ids(self.df, self.fcn)
        dsc.add_pair_id(self.df, self.fcn, self.pair_ids, inplace=True)

        self.direction_ids = dsc.create_direction_ids(self.df, self.fcn)
        dsc.add_direction_id(self.df, self.fcn, self.direction_ids, inplace=True)

        self.master_station_id = self.detect_master_staion()

    def detect_master_staion(self) -> int | None:
        """Try to detect the master station by its port. Return the first found with corresponding port.

        Returns
        -------
        int | None
            ID of master station. None if not found.
        """
        for station_id, station in self.station_ids.items():
            if self.fcn.double_column_station:
                if station.port == MASTER_STATION_PORT:
                    return station_id
            else:
                if str(MASTER_STATION_PORT) in station.ip:
                    return station_id
        else:
            return None

    def get_event_data(self) -> EventData:
        # TODO dokumentace
        data = EventData(
            self.df,
            self.fcn,
            self.file_path,
            self.original_cols,
            self.station_ids,
            self.pair_ids,
            self.direction_ids,
            self.master_station_id,
            self.slave_stations,
        )
        return data

    # endregion

    # region Toolbar

    def create_toolbar(self) -> QToolBar:
        """Initialize toolbar with actions.

        Add all defined actions to toolbar.

        Notes
        -----
        Should be called after create_actions().

        Returns
        -------
        QToolBar
            Toolbar with actions.
        """
        assert self.actions

        toolbar = QToolBar("Main toolbar", self)
        toolbar.setMovable(False)

        for action in self.actions.values():
            toolbar.addAction(action)

        return toolbar

    def create_actions(self) -> dict[str, QAction]:
        """Create actions and connect them to triggers (buttons etc.).

        Returns
        -------
        dict[str, QAction]
            Key : Action name.
            Value : QAction object.
            Actions used in menu and toolbar.
        """
        actions = dict()

        # LOAD CSV #
        name = "Load CSV"
        actions[name] = QAction(icon=QIcon("gui/icons/file.png"), text=name, parent=self)
        # https://www.iconfinder.com/icons/290138/document_extension_file_format_paper_icon
        actions[name].triggered.connect(self.load_csv)

        # SELECT MASTER STATION #
        name = "Select master station"
        actions[name] = QAction(icon=QIcon("gui/icons/computa.png"), text=name, parent=self)
        actions[name].triggered.connect(self.select_master_station)

        # SELECT PAIRS #
        name = "Select pairs"
        actions[name] = QAction(icon=QIcon("gui/icons/computa.png"), text=name, parent=self)
        actions[name].triggered.connect(self.select_slaves)

        # EXIT #
        name = "Exit"
        actions[name] = QAction(icon=QIcon("gui/icons/exit.png"), text=name, parent=self)
        # https://www.iconfinder.com/icons/352328/app_exit_to_icon
        actions[name].triggered.connect(QApplication.instance().quit)  # TODO je to spravne?

        return actions

        # endregion
