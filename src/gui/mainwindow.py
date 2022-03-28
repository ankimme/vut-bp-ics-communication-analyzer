"""This file contains code of the main window of the application.

Author
------
Andrea Chimenti

Date
----
March 2022
"""

from multiprocessing.sharedctypes import Value
from bidict import bidict
import pandas as pd

from PyQt6.QtWidgets import QMainWindow, QApplication, QToolBar, QFileDialog, QTabWidget, QMessageBox
from PyQt6.QtGui import QIcon, QAction

from dsmanipulator import dsloader as dsl
from dsmanipulator import dscreator as dsc
from dsmanipulator import dsanalyzer as dsa

from gui.components import OpenCsvWizard
from gui.tabs import OriginalDfTab, StatsTab, PairPlotsTab, SlavesPlotTab, TimeFrameViewTab, AttributeStatsTab
from gui.utils import EventType, EventHandler, EventData
from gui.components import SelectMasterStationsDialog, SelectSlavesDialog, ChangeResampleRate, SelectAttributeDialog
from dsmanipulator.utils import Direction, Station, FileColumnNames


class MainWindow(QMainWindow):
    """Main application window.

    Attributes
    ----------
    actions : dict[str, QAction]
        Actions used in menu and toolbar.
    df : pd.DataFrame
        Original dataframe loaded from csv.
    filtered_df : pd.DataFrame
        Dataframe containing only communication between selected master and slaves.
    fcn : FileColumnNames
        Real names of predefined columns.
    event_handler : EventHandler
        A simple event handler for events that should change data in UI.
    resample_rate : pd.Timedelta
        Timespan used for data analysis.
    original_cols : list[str]
        Columns that where part of the original csv file.
    attribute_name : str
        Attribute of interest used in analysis.
    file_path : str
        File path of the csv file.
    master_station_id : int
        ID of station that should be treated as master.
    slave_station_ids : list[int]
        IDs of stations that should be treated as slaves.
    station_ids : bidict[int, Station]
        Key : ID of station.
        Value : Station.
    pair_ids : bidict[int, frozenset]
        Key : ID of station.
        Value : Pair of station ids.
        Direction does not matter.
    direction_ids : bidict[int, Direction]
        Key : ID of station.
        Value : Pair of station ids. Source and destination.
        Direction does matter.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ICS Analyzer")
        self.setMinimumSize(800, 500)

        self.actions = self.create_actions()
        self.df: pd.DataFrame = None
        self.filtered_df: pd.DataFrame = None
        self.fcn: FileColumnNames
        self.event_handler = EventHandler()
        self.resample_rate: pd.Timedelta = pd.Timedelta(minutes=5)
        self.original_cols: list[str]
        self.attribute_name: str = None
        self.file_path: str
        self.master_station_id: int
        self.slave_station_ids: list[int] = []
        self.station_ids: bidict[int, Station]
        self.pair_ids: bidict[int, frozenset]
        self.direction_ids: bidict[int, Direction]

        toolbar = self.create_toolbar()
        self.addToolBar(toolbar)

        tabs = QTabWidget()

        # TAB 1 #
        original_df_tab = OriginalDfTab(self)
        self.event_handler.subscribe(EventType.DATAFRAME_CHANGED, original_df_tab.update_model)
        tabs.addTab(original_df_tab, "Original Dataframe")

        # TAB 2 #

        stats_tab = StatsTab(self)
        self.event_handler.subscribe(EventType.DATAFRAME_CHANGED, stats_tab.update_stats)
        self.event_handler.subscribe(EventType.MASTER_SLAVES_CHANGED, stats_tab.update_master_station)
        tabs.addTab(stats_tab, "General statistics")

        # TAB 3 #

        pair_plots_tab = PairPlotsTab(self)
        self.event_handler.subscribe(EventType.DATAFRAME_CHANGED, pair_plots_tab.update_plots)
        self.event_handler.subscribe(EventType.MASTER_SLAVES_CHANGED, pair_plots_tab.update_plots)
        self.event_handler.subscribe(EventType.RESAMPLE_RATE_CHANGED, pair_plots_tab.update_plots)
        tabs.addTab(pair_plots_tab, "Communication pairs")

        # TAB 4 #
        slave_plots_tab = SlavesPlotTab(self.actions["Select master station"], self)  # TODO delete first param
        self.event_handler.subscribe(EventType.DATAFRAME_CHANGED, slave_plots_tab.update_plots)
        self.event_handler.subscribe(EventType.MASTER_SLAVES_CHANGED, slave_plots_tab.update_plots)
        self.event_handler.subscribe(EventType.RESAMPLE_RATE_CHANGED, slave_plots_tab.update_plots)
        tabs.addTab(slave_plots_tab, "Slave communication")

        # TAB 5 #
        time_frame_view_tab = TimeFrameViewTab(self)
        self.event_handler.subscribe(EventType.DATAFRAME_CHANGED, time_frame_view_tab.update_model)
        self.event_handler.subscribe(EventType.MASTER_SLAVES_CHANGED, time_frame_view_tab.update_model)
        self.event_handler.subscribe(EventType.RESAMPLE_RATE_CHANGED, time_frame_view_tab.update_model)
        self.event_handler.subscribe(EventType.ATTRIBUTE_CHANGED, time_frame_view_tab.update_model)
        tabs.addTab(time_frame_view_tab, "Time frame view")

        # TAB 6 #
        attribute_stats_tab = AttributeStatsTab(self)
        self.event_handler.subscribe(EventType.DATAFRAME_CHANGED, attribute_stats_tab.update_plots)
        self.event_handler.subscribe(EventType.MASTER_SLAVES_CHANGED, attribute_stats_tab.update_plots)
        self.event_handler.subscribe(EventType.RESAMPLE_RATE_CHANGED, attribute_stats_tab.update_plots)
        self.event_handler.subscribe(EventType.ATTRIBUTE_CHANGED, attribute_stats_tab.update_plots)
        tabs.addTab(attribute_stats_tab, "Attribute stats")

        self.setCentralWidget(tabs)

    # region Actions

    def load_csv(self) -> None:
        """Open dialog for loading data from a CSV file.

        If a file is loaded, preprocess the dataframe, update self attributes and notify observers.
        """

        # TODO delete test
        if True:
            self.file_path = "placeholder.py"
            import pickle

            with open("../save/fcn.pkl", "rb") as f:
                self.fcn = pickle.load(f)
            self.df = pd.read_pickle("../save/df.pkl")
            self.original_cols = self.df.columns

            self.preprocess_df()

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
                try:
                    self.df = dsl.load_data(file_path, dtype, dialect)
                except ValueError as e:
                    dlg = QMessageBox(self)
                    dlg.setWindowTitle("Error")
                    dlg.setText(str(e))
                    dlg.setIcon(QMessageBox.Icon.Warning)
                    dlg.exec()
                    return

                self.df.to_pickle("../save/df3.pkl")  # TODO delete
                self.original_cols = self.df.columns

                self.preprocess_df()

                data = self.get_event_data()
                self.event_handler.notify(EventType.DATAFRAME_CHANGED, data)

                # # TODO delete
                import pickle

                with open("../save/fcn.pkl", "wb") as f:
                    pickle.dump(self.fcn, f)

    def change_master_station(self) -> None:
        """Open dialog for master station selection.

        If a new master station is selected, update the self.master_station_id and notify observers about the change.
        """
        if self.df is not None:
            dlg = SelectMasterStationsDialog(self.station_ids, self.master_station_id, parent=self)
            if dlg.exec():
                self.master_station_id = dlg.get_master_station_id()
                self.slave_station_ids = dsa.get_connected_stations(self.pair_ids, self.master_station_id)

                filtered_pair_ids = dsa.get_connected_pairs(
                    self.master_station_id, self.slave_station_ids, self.pair_ids
                )
                self.filtered_df = self.df[self.df[self.fcn.pair_id].isin(filtered_pair_ids)]

                data = self.get_event_data()
                self.event_handler.notify(EventType.MASTER_SLAVES_CHANGED, data)
        else:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Warning")
            dlg.setText("Please load a CSV file before proceeding")
            dlg.setIcon(QMessageBox.Icon.Warning)
            dlg.exec()

    def change_slaves(self) -> None:
        """Open dialog for slave stations selection.

        If new slave stations are selected, update the self.slave_station_ids and notify observers about the change.
        """
        if self.df is not None:
            dlg = SelectSlavesDialog(
                self.master_station_id, self.slave_station_ids, self.station_ids, self.pair_ids, parent=self
            )
            if dlg.exec():
                self.slave_station_ids = dlg.get_slave_stations_ids()

                filtered_pair_ids = dsa.get_connected_pairs(
                    self.master_station_id, self.slave_station_ids, self.pair_ids
                )
                self.filtered_df = self.df[self.df[self.fcn.pair_id].isin(filtered_pair_ids)]

                data = self.get_event_data()
                self.event_handler.notify(EventType.MASTER_SLAVES_CHANGED, data)
        else:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Warning")
            dlg.setText("Please load a CSV file before proceeding")
            dlg.setIcon(QMessageBox.Icon.Warning)
            dlg.exec()

    def change_resample_rate(self) -> None:

        if self.df is not None:
            dlg = ChangeResampleRate(self.resample_rate, parent=self)
            if dlg.exec():
                self.resample_rate = dlg.get_resample_rate()

                data = self.get_event_data()
                self.event_handler.notify(EventType.RESAMPLE_RATE_CHANGED, data)
        else:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Warning")
            dlg.setText("Please load a CSV file before proceeding")
            dlg.setIcon(QMessageBox.Icon.Warning)
            dlg.exec()

    def change_attribute_name(self) -> None:

        if self.df is not None:
            filtered_attributes = list(set(self.original_cols) - set(self.fcn.predefined_cols))
            dlg = SelectAttributeDialog(self.attribute_name, filtered_attributes, parent=self)
            if dlg.exec():
                self.attribute_name = dlg.get_attribute_name()

                data = self.get_event_data()
                self.event_handler.notify(EventType.ATTRIBUTE_CHANGED, data)
        else:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Warning")
            dlg.setText("Please load a CSV file before proceeding")
            dlg.setIcon(QMessageBox.Icon.Warning)
            dlg.exec()

    # endregion

    # region Utilities

    def preprocess_df(self) -> None:
        """Prepare the dataframe for further use in the app.

        Also create or update attributes used in the rest of the code of the app.
        """
        dsc.add_relative_days(self.df, self.fcn, inplace=True)

        self.station_ids = dsc.create_station_ids(self.df, self.fcn)
        dsc.add_station_id(self.df, self.fcn, self.station_ids, inplace=True)

        self.pair_ids = dsc.create_pair_ids(self.df, self.fcn)
        dsc.add_pair_id(self.df, self.fcn, self.pair_ids, inplace=True)

        self.direction_ids = dsc.create_direction_ids(self.df, self.fcn)
        dsc.add_direction_id(self.df, self.fcn, self.direction_ids, inplace=True)

        self.master_station_id = dsa.detect_master_staion(self.station_ids, self.fcn.double_column_station)
        self.slave_station_ids = dsa.get_connected_stations(self.pair_ids, self.master_station_id)

        filtered_pair_ids = dsa.get_connected_pairs(self.master_station_id, self.slave_station_ids, self.pair_ids)
        self.filtered_df = self.df[self.df[self.fcn.pair_id].isin(filtered_pair_ids)]

    # def detect_master_staion(self) -> int | None:
    #     """Try to detect the master station by its port. Return the first found with corresponding port.

    #     Returns
    #     -------
    #     int | None
    #         ID of master station. None if not found.
    #     """
    #     for station_id, station in self.station_ids.items():
    #         if self.fcn.double_column_station:
    #             if station.port == MASTER_STATION_PORT:
    #                 return station_id
    #         else:
    #             if str(MASTER_STATION_PORT) in station.ip:
    #                 return station_id
    #     else:
    #         return None

    def get_event_data(self) -> EventData:
        """Prepare event data.

        Returns
        -------
        EventData
            Data used by events.
        """
        data = EventData(
            self.df,
            self.filtered_df,
            self.fcn,
            self.file_path,
            self.resample_rate,
            self.original_cols,
            self.attribute_name,
            self.station_ids,
            self.pair_ids,
            self.direction_ids,
            self.master_station_id,
            self.slave_station_ids,
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
        actions[name].triggered.connect(self.change_master_station)

        # SELECT PAIRS #
        name = "Select pairs"
        actions[name] = QAction(icon=QIcon("gui/icons/computa.png"), text=name, parent=self)
        actions[name].triggered.connect(self.change_slaves)

        # CHANGE RESAMPLE RATE #
        name = "Change resample rate"
        actions[name] = QAction(icon=QIcon("gui/icons/computa.png"), text=name, parent=self)
        actions[name].triggered.connect(self.change_resample_rate)

        # CHANGE ATTRIBUTE OF INTEREST #
        name = "Change attribute"
        actions[name] = QAction(icon=QIcon("gui/icons/computa.png"), text=name, parent=self)
        actions[name].triggered.connect(self.change_attribute_name)

        # EXIT #
        name = "Exit"
        actions[name] = QAction(icon=QIcon("gui/icons/exit.png"), text=name, parent=self)
        # https://www.iconfinder.com/icons/352328/app_exit_to_icon
        actions[name].triggered.connect(QApplication.instance().quit)  # TODO je to spravne?

        return actions

        # endregion
