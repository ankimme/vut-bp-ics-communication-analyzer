"""This file contains code of the main window of the application.

Author
------
Andrea Chimenti

Date
----
March 2022
"""

import os
import pandas as pd
from datetime import datetime
from bidict import bidict

from PyQt6.QtCore import Qt, QThread, pyqtSlot
from PyQt6.QtWidgets import (
    QMainWindow,
    QApplication,
    QToolBar,
    QMenuBar,
    QFileDialog,
    QTabWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
    QMessageBox,
)
from PyQt6.QtGui import QAction, QFont

from dsmanipulator import dscreator as dsc
from dsmanipulator import dsanalyzer as dsa
from dsmanipulator.dataobjects import Direction, Station, FileColumnNames, DirectionEnum

from app.workers import LoadCsvWorker
from app.opencsvwizard import OpenCsvWizard
from app.widgets import SettingsPanelWidget
from app.qtwaitingspinner import QtWaitingSpinner
from app.tabs import OriginalDfTab, StatsTab, PairPlotsTab, SlavesPlotTab, TimeFrameViewTab, AttributeStatsTab
from app.eventhandler import EventType, EventHandler, EventData
from app.dialogs import (
    SelectMasterStationsDialog,
    SelectSlavesDialog,
    ChangeResampleRateDialog,
    SelectAttributeDialog,
    SelectAttributeValuesDialog,
    WarningMessageBox,
    ChangeIntervalDialog,
    ChangeDirectionDialog,
)


class MainWindow(QMainWindow):
    """Main application window.

    Attributes
    ----------
    actions : dict[str, QAction]
        Actions used in menu and toolbar.
    df_working : pd.DataFrame
        Original dataframe with custom columns.
    fcn : FileColumnNames
        Real names of predefined columns.
    event_handler : EventHandler
        A simple event handler for events that should change data in UI.
    resample_rate : pd.Timedelta
        Timespan used for data analysis.
    og_cols : list[str]
        Columns that where part of the original csv file.
    attribute_name : str
        Attribute of interest used in analysis.
    attribute_values : list[str | int | float]
        Selected values of attribute.
    direction : DirectionEnum
        Selected direction of communication.
    start_dt : datetime
        Start time of communication.
    end_dt:  datetime
        Start time of communication.
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
        Key : ID of pair.
        Value : Pair of station ids.
        Direction does not matter.
    direction_ids : bidict[int, Direction]
        Key : ID of direction.
        Value : Pair of station ids. Source and destination.
        Direction does matter.

    Properties
    ----------
    df_og : pd.DataFrame
        Original dataframe loaded from csv.
    df_filtered : pd.DataFrame
        Working dataframe with applied user filters.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ICS Analyzer")
        self.setMinimumSize(800, 600)
        self.setFont(QFont("Monospace"))

        self.actions = self.create_actions()
        self.df_working: pd.DataFrame = None
        self.fcn: FileColumnNames
        self.event_handler = EventHandler()
        self.resample_rate: pd.Timedelta = pd.Timedelta(minutes=5)
        self.og_cols: list[str]
        self.attribute_name: str = None
        self.attribute_values: list[str | int | float] = []
        self.direction: DirectionEnum = DirectionEnum.BOTH
        self.start_dt: datetime
        self.end_dt: datetime
        self.file_path: str
        self.master_station_id: int
        self.slave_station_ids: list[int] = []
        self.station_ids: bidict[int, Station]
        self.pair_ids: bidict[int, frozenset]
        self.direction_ids: bidict[int, Direction]

        main_layout = QVBoxLayout()

        # MENU BAR

        menuBar = self.create_menubar()
        self.setMenuBar(menuBar)

        # SETTINGS PANEL

        main_layout.addWidget(QLabel("APPLIED SETTINGS"))

        settings_layout = QHBoxLayout()

        settings_panel = SettingsPanelWidget(parent=self)
        self.event_handler.subscribe(EventType.DATAFRAME_CHANGED, settings_panel.update_panel)
        self.event_handler.subscribe(EventType.MASTER_SLAVES_CHANGED, settings_panel.update_panel)
        self.event_handler.subscribe(EventType.DIRECTION_CHANGED, settings_panel.update_panel)
        self.event_handler.subscribe(EventType.INTERVAL_CHANGED, settings_panel.update_panel)
        self.event_handler.subscribe(EventType.RESAMPLE_RATE_CHANGED, settings_panel.update_panel)
        self.event_handler.subscribe(EventType.ATTRIBUTE_CHANGED, settings_panel.update_panel)
        self.event_handler.subscribe(EventType.ATTRIBUTE_VALUES_CHANGED, settings_panel.update_panel)
        main_layout.addWidget(settings_panel)

        # TABS

        tabs = QTabWidget(parent=self)

        # TAB 1 #
        original_df_tab = OriginalDfTab(self)
        self.event_handler.subscribe(EventType.DATAFRAME_CHANGED, original_df_tab.update_model)
        self.event_handler.subscribe(EventType.MASTER_SLAVES_CHANGED, original_df_tab.update_model)
        self.event_handler.subscribe(EventType.DIRECTION_CHANGED, original_df_tab.update_model)
        self.event_handler.subscribe(EventType.INTERVAL_CHANGED, original_df_tab.update_model)
        self.event_handler.subscribe(EventType.ATTRIBUTE_CHANGED, original_df_tab.update_model)
        self.event_handler.subscribe(EventType.ATTRIBUTE_VALUES_CHANGED, original_df_tab.update_model)
        tabs.addTab(original_df_tab, "Dataset table")

        # TAB 2 #

        stats_tab = StatsTab(self)
        self.event_handler.subscribe(EventType.DATAFRAME_CHANGED, stats_tab.update_og_stats)

        self.event_handler.subscribe(EventType.DATAFRAME_CHANGED, stats_tab.update_work_stats)
        self.event_handler.subscribe(EventType.MASTER_SLAVES_CHANGED, stats_tab.update_work_stats)
        self.event_handler.subscribe(EventType.DIRECTION_CHANGED, stats_tab.update_work_stats)
        self.event_handler.subscribe(EventType.INTERVAL_CHANGED, stats_tab.update_work_stats)
        self.event_handler.subscribe(EventType.ATTRIBUTE_CHANGED, stats_tab.update_work_stats)
        self.event_handler.subscribe(EventType.ATTRIBUTE_VALUES_CHANGED, stats_tab.update_work_stats)

        tabs.addTab(stats_tab, "General statistics")

        # TAB 3 #

        pair_plots_tab = PairPlotsTab(self)
        self.event_handler.subscribe(EventType.DATAFRAME_CHANGED, pair_plots_tab.update_plots)
        self.event_handler.subscribe(EventType.RESAMPLE_RATE_CHANGED, pair_plots_tab.update_plots)
        self.event_handler.subscribe(EventType.INTERVAL_CHANGED, pair_plots_tab.update_plots)
        tabs.addTab(pair_plots_tab, "All pairs")

        # TAB 4 #
        slave_plots_tab = SlavesPlotTab(self)
        self.event_handler.subscribe(EventType.DATAFRAME_CHANGED, slave_plots_tab.update_tab)
        self.event_handler.subscribe(EventType.MASTER_SLAVES_CHANGED, slave_plots_tab.update_tab)
        self.event_handler.subscribe(EventType.RESAMPLE_RATE_CHANGED, slave_plots_tab.update_tab)
        self.event_handler.subscribe(EventType.DIRECTION_CHANGED, slave_plots_tab.update_tab)
        self.event_handler.subscribe(EventType.INTERVAL_CHANGED, slave_plots_tab.update_tab)
        self.event_handler.subscribe(EventType.ATTRIBUTE_CHANGED, slave_plots_tab.update_tab)
        self.event_handler.subscribe(EventType.ATTRIBUTE_VALUES_CHANGED, slave_plots_tab.update_tab)
        tabs.addTab(slave_plots_tab, "Selected slaves")

        # TAB 5 #
        time_frame_view_tab = TimeFrameViewTab(self)
        self.event_handler.subscribe(EventType.DATAFRAME_CHANGED, time_frame_view_tab.update_model)
        self.event_handler.subscribe(EventType.MASTER_SLAVES_CHANGED, time_frame_view_tab.update_model)
        self.event_handler.subscribe(EventType.DIRECTION_CHANGED, time_frame_view_tab.update_model)
        self.event_handler.subscribe(EventType.INTERVAL_CHANGED, time_frame_view_tab.update_model)
        self.event_handler.subscribe(EventType.RESAMPLE_RATE_CHANGED, time_frame_view_tab.update_model)
        self.event_handler.subscribe(EventType.ATTRIBUTE_CHANGED, time_frame_view_tab.update_model)
        self.event_handler.subscribe(EventType.ATTRIBUTE_VALUES_CHANGED, time_frame_view_tab.update_model)
        tabs.addTab(time_frame_view_tab, "Attribute table")

        # TAB 6 #
        attribute_stats_tab = AttributeStatsTab(self)
        self.event_handler.subscribe(EventType.DATAFRAME_CHANGED, attribute_stats_tab.update_tab)
        self.event_handler.subscribe(EventType.MASTER_SLAVES_CHANGED, attribute_stats_tab.update_tab)
        self.event_handler.subscribe(EventType.DIRECTION_CHANGED, attribute_stats_tab.update_tab)
        self.event_handler.subscribe(EventType.INTERVAL_CHANGED, attribute_stats_tab.update_tab)
        self.event_handler.subscribe(EventType.RESAMPLE_RATE_CHANGED, attribute_stats_tab.update_tab)
        self.event_handler.subscribe(EventType.RESAMPLE_RATE_CHANGED, attribute_stats_tab.update_tab)
        self.event_handler.subscribe(EventType.ATTRIBUTE_CHANGED, attribute_stats_tab.update_tab)
        self.event_handler.subscribe(EventType.ATTRIBUTE_VALUES_CHANGED, attribute_stats_tab.update_tab)
        tabs.addTab(attribute_stats_tab, "Attribute statistics")

        main_layout.addWidget(tabs)

        main_widget = QWidget()
        main_widget.setLayout(main_layout)

        self.setCentralWidget(main_widget)

    # region Properties

    @property
    def df_og(self) -> pd.DataFrame:
        """Original dataframe loaded from csv."""
        if self.df_working is not None:
            return self.df_working.loc[:, self.og_cols]
        else:
            return None

    @property
    def df_filtered(self) -> pd.DataFrame:
        """Working dataframe with applied user filters.

        Filtered by:
        - Selected master and slaves
        - Direction
        - Interval
        - Attribute
        """
        if self.df_working is not None:
            filtered_pair_ids = dsa.get_connected_pairs(self.master_station_id, self.slave_station_ids, self.pair_ids)

            filtered_direction_ids = dsa.get_direction_ids_by_filter(
                self.master_station_id, self.slave_station_ids, self.direction, self.direction_ids
            )

            if self.attribute_name is not None:

                return self.df_working[
                    (self.df_working[self.fcn.pair_id].isin(filtered_pair_ids))
                    & (self.df_working[self.fcn.direction_id].isin(filtered_direction_ids))
                    & (self.df_working[self.fcn.timestamp].between(self.start_dt, self.end_dt))
                    & (self.df_working[self.attribute_name].isin(self.attribute_values))
                ]

            else:
                return self.df_working[
                    (self.df_working[self.fcn.pair_id].isin(filtered_pair_ids))
                    & (self.df_working[self.fcn.direction_id].isin(filtered_direction_ids))
                    & (self.df_working[self.fcn.timestamp].between(self.start_dt, self.end_dt))
                ]

        else:
            return None

    @property
    def event_data(self) -> EventData:
        """Event data object."""
        data = EventData(
            self.df_working,
            self.df_og,
            self.df_filtered,
            self.fcn,
            self.file_path,
            self.resample_rate,
            self.attribute_name,
            self.attribute_values,
            self.direction,
            self.start_dt,
            self.end_dt,
            self.station_ids,
            self.pair_ids,
            self.direction_ids,
            self.master_station_id,
            self.slave_station_ids,
        )
        return data

    # endregion

    # region Actions

    @pyqtSlot(pd.DataFrame)
    def load_csv_from_worker(self, df: pd.DataFrame) -> None:
        """Action after csv is loaded"""
        self.df_working = df
        self.preprocess_df()
        self.setWindowTitle(f"ICS Analyzer - {os.path.basename(self.file_path)}")
        self.event_handler.notify(EventType.DATAFRAME_CHANGED, self.event_data)

    def load_csv(self) -> None:
        """Open dialog for loading data from a CSV file.

        If a file is loaded, preprocess the dataframe, update self attributes and notify observers.
        """

        file_path, _ = QFileDialog.getOpenFileName(parent=self, caption="Open file", filter="CSV files (*.csv *.txt)")

        if file_path:
            self.file_path = file_path
            dialog = OpenCsvWizard(file_path)
            if dialog.exec():
                dialect, data_types, self.fcn = dialog.get_csv_settings()

                self.thread = QThread()
                self.worker = LoadCsvWorker(file_path, data_types, dialect)
                self.worker.moveToThread(self.thread)

                self.thread.started.connect(self.worker.load_csv)

                self.worker.csv_loaded.connect(self.load_csv_from_worker)
                self.worker.exception_raised.connect(
                    lambda: WarningMessageBox("Could not load CSV file with given configuartion", self).exec()
                )

                self.worker.finished.connect(self.thread.quit)
                self.worker.finished.connect(self.worker.deleteLater)
                self.thread.finished.connect(self.thread.deleteLater)
                self.thread.finished.connect(lambda: self.spinner.stop())

                self.spinner = QtWaitingSpinner(self, True, True, Qt.WindowModality.ApplicationModal)
                self.spinner.start()
                self.thread.start()

    def show_help(self) -> None:
        "Show help dialog"
        dlg = QMessageBox()
        dlg.setWindowTitle("Help")
        dlg.setText("To be done")
        dlg.exec()

    def show_about(self) -> None:
        "Show about dialog"
        dlg = QMessageBox()
        dlg.setWindowTitle("About")
        dlg.setText("Andrea Chimenti\nBrno University of Technology\n2022")
        dlg.exec()

    def change_master_station(self) -> None:
        """Open dialog for master station selection.

        If a new master station is selected, update the self.master_station_id and notify observers about the change.
        """
        if self.df_working is not None:
            dlg = SelectMasterStationsDialog(self.station_ids, self.master_station_id, parent=self)
            if dlg.exec():
                self.master_station_id = dlg.get_master_station_id()
                self.slave_station_ids = dsa.get_connected_stations(self.pair_ids, self.master_station_id)

                self.event_handler.notify(EventType.MASTER_SLAVES_CHANGED, self.event_data)
        else:
            WarningMessageBox("Please load a CSV file before proceeding", self).exec()

    def change_slaves(self) -> None:
        """Open dialog for slave stations selection.

        If new slave stations are selected, update the self.slave_station_ids and notify observers about the change.
        """
        if self.df_working is not None:
            dlg = SelectSlavesDialog(
                self.master_station_id, self.slave_station_ids, self.station_ids, self.pair_ids, parent=self
            )
            if dlg.exec():
                self.slave_station_ids = dlg.get_slave_stations_ids()

                self.event_handler.notify(EventType.MASTER_SLAVES_CHANGED, self.event_data)
        else:
            WarningMessageBox("Please load a CSV file before proceeding", self).exec()

    def change_direction(self) -> None:
        if self.df_working is not None:
            dlg = ChangeDirectionDialog(og_direction=self.direction, parent=self)

            if dlg.exec():
                self.direction = dlg.get_direction()

                self.event_handler.notify(EventType.DIRECTION_CHANGED, self.event_data)
        else:
            WarningMessageBox("Please load a CSV file before proceeding", self).exec()

    def change_interval(self) -> None:
        if self.df_working is not None:
            dlg = ChangeIntervalDialog(
                start=self.start_dt,
                end=self.end_dt,
                low_limit=self.df_working[self.fcn.timestamp].iloc[0],
                upper_limit=self.df_working[self.fcn.timestamp].iloc[-1],
                parent=self,
            )
            if dlg.exec():
                self.start_dt, self.end_dt = dlg.get_new_interval()
                self.event_handler.notify(EventType.INTERVAL_CHANGED, self.event_data)
        else:
            WarningMessageBox("Please load a CSV file before proceeding", self).exec()

    def change_resample_rate(self) -> None:

        if self.df_working is not None:
            dlg = ChangeResampleRateDialog(self.resample_rate, parent=self)
            if dlg.exec():
                self.resample_rate = dlg.get_resample_rate()

                self.event_handler.notify(EventType.RESAMPLE_RATE_CHANGED, self.event_data)
        else:
            WarningMessageBox("Please load a CSV file before proceeding", self).exec()

    def change_attribute_name(self) -> None:

        if self.df_working is not None:
            filtered_attributes = list(set(self.og_cols) - set(self.fcn.predefined_cols))
            dlg = SelectAttributeDialog(self.attribute_name, filtered_attributes, parent=self)
            if dlg.exec():
                self.attribute_name = dlg.get_attribute_name()

                # automatically select all
                if self.attribute_name is not None:
                    self.attribute_values = self.df_working[self.attribute_name].dropna().unique()
                else:
                    self.attribute_values = []

                self.event_handler.notify(EventType.ATTRIBUTE_CHANGED, self.event_data)
        else:
            WarningMessageBox("Please load a CSV file before proceeding", self).exec()

    def select_attribute_values(self) -> None:

        if self.df_working is not None:

            if self.attribute_name is not None:

                dlg = SelectAttributeValuesDialog(
                    self.attribute_values, self.df_working[self.attribute_name].dropna().unique(), parent=self
                )
                if dlg.exec():
                    self.attribute_values = dlg.get_attribute_values()

                    self.event_handler.notify(EventType.ATTRIBUTE_VALUES_CHANGED, self.event_data)
            else:
                WarningMessageBox("Please select an attribute before proceeding", self).exec()
        else:
            WarningMessageBox("Please load a CSV file before proceeding", self).exec()

    # endregion

    # region Utilities

    def preprocess_df(self) -> None:
        """Prepare the dataframe for further use in the app.

        Also create or update attributes used in the rest of the code of the app.
        """
        self.og_cols = self.df_working.columns

        self.direction = DirectionEnum.BOTH
        self.attribute_name = None
        self.attribute_values = []
        self.resample_rate = pd.Timedelta(minutes=5)

        dsc.add_relative_days(self.df_working, self.fcn, inplace=True)

        self.start_dt = self.df_working[self.fcn.timestamp].iloc[0]
        self.end_dt = self.df_working[self.fcn.timestamp].iloc[-1]

        self.station_ids = dsc.create_station_ids(self.df_working, self.fcn)
        dsc.add_station_id(self.df_working, self.fcn, self.station_ids, inplace=True)

        self.pair_ids = dsc.create_pair_ids(self.df_working, self.fcn)
        dsc.add_pair_id(self.df_working, self.fcn, self.pair_ids, inplace=True)

        self.direction_ids = dsc.create_direction_ids(self.df_working, self.fcn)
        dsc.add_direction_id(self.df_working, self.fcn, self.direction_ids, inplace=True)

        self.master_station_id = dsa.detect_master_staion(self.station_ids, self.fcn.double_column_station)
        self.slave_station_ids = dsa.get_connected_stations(self.pair_ids, self.master_station_id)

    # endregion

    # region Menu & Toolbar

    def create_menubar(self) -> QMenuBar:
        assert self.actions

        menubar = QMenuBar()

        fileMenu = menubar.addMenu("&File")
        filterMenu = menubar.addMenu("&Filter")
        helpMenu = menubar.addMenu("&Help")

        for action_name, qaction in self.actions.items():
            match action_name:
                case "Load CSV" | "Exit":
                    fileMenu.addAction(qaction)
                case "Show help" | "About":
                    helpMenu.addAction(qaction)
                case _:
                    filterMenu.addAction(qaction)

        return menubar

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
        actions[name] = QAction(text=name, parent=self)
        actions[name].triggered.connect(self.load_csv)

        # SHOW HELP #
        name = "Show help"
        actions[name] = QAction(text=name, parent=self)
        actions[name].triggered.connect(self.show_help)

        # SHOW HELP #
        name = "About"
        actions[name] = QAction(text=name, parent=self)
        actions[name].triggered.connect(self.show_about)

        # SELECT MASTER STATION #
        name = "Select master station"
        actions[name] = QAction(text=name, parent=self)
        actions[name].triggered.connect(self.change_master_station)

        # SELECT SLAVES #
        name = "Select slaves"
        actions[name] = QAction(text=name, parent=self)
        actions[name].triggered.connect(self.change_slaves)

        # SELECT DIRECTION #
        name = "Select direction"
        actions[name] = QAction(text=name, parent=self)
        actions[name].triggered.connect(self.change_direction)

        # CHANGE INTERVAL #
        name = "Change  start and end time"
        actions[name] = QAction(text=name, parent=self)
        actions[name].triggered.connect(self.change_interval)

        # CHANGE RESAMPLE RATE #
        name = "Change time window size"
        actions[name] = QAction(text=name, parent=self)
        actions[name].triggered.connect(self.change_resample_rate)

        # CHANGE ATTRIBUTE OF INTEREST #
        name = "Select attribute"
        actions[name] = QAction(text=name, parent=self)
        actions[name].triggered.connect(self.change_attribute_name)

        # SELECT ATTRIBUTE VALUES #
        name = "Select attribute values"
        actions[name] = QAction(text=name, parent=self)
        actions[name].triggered.connect(self.select_attribute_values)

        # EXIT #
        name = "Exit"
        actions[name] = QAction(text=name, parent=self)
        # https://www.iconfinder.com/icons/352328/app_exit_to_icon
        actions[name].triggered.connect(QApplication.instance().quit)

        return actions

        # endregion
