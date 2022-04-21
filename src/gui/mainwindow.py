"""This file contains code of the main window of the application.

Author
------
Andrea Chimenti

Date
----
March 2022
"""

from datetime import datetime
from bidict import bidict
import pandas as pd

from PyQt6.QtWidgets import (
    QMainWindow,
    QApplication,
    QToolBar,
    QFileDialog,
    QTabWidget,
    QMessageBox,
    QVBoxLayout,
    QLabel,
    QWidget,
)
from PyQt6.QtGui import QIcon, QAction, QFont

from dsmanipulator import dsloader as dsl
from dsmanipulator import dscreator as dsc
from dsmanipulator import dsanalyzer as dsa

from gui.components import OpenCsvWizard, SettingsPanelWidget
from gui.tabs import OriginalDfTab, StatsTab, PairPlotsTab, SlavesPlotTab, TimeFrameViewTab, AttributeStatsTab
from gui.utils import EventType, EventHandler, EventData
from gui.components import (
    SelectMasterStationsDialog,
    SelectSlavesDialog,
    ChangeResampleRateDialog,
    SelectAttributeDialog,
    LoadWarningMessageBox,
    ChangeIntervalDialog,
    ChangeDirectionDialog,
)
from dsmanipulator.utils import Direction, Station, FileColumnNames, DirectionEnum


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
        self.direction: DirectionEnum = DirectionEnum.BOTH  # TODO doc
        self.start_dt: datetime  # TODO doc
        self.end_dt: datetime
        self.file_path: str
        self.master_station_id: int
        self.slave_station_ids: list[int] = []
        self.station_ids: bidict[int, Station]
        self.pair_ids: bidict[int, frozenset]
        self.direction_ids: bidict[int, Direction]

        main_layout = QVBoxLayout()

        # TOOLBAR

        toolbar = self.create_toolbar()
        self.addToolBar(toolbar)

        # SETTINGS PANEL

        main_layout.addWidget(QLabel("APPLIED SETTINGS"))

        settings_panel = SettingsPanelWidget(parent=self)
        self.event_handler.subscribe(EventType.DATAFRAME_CHANGED, settings_panel.update_panel)
        self.event_handler.subscribe(EventType.MASTER_SLAVES_CHANGED, settings_panel.update_panel)
        self.event_handler.subscribe(EventType.DIRECTION_CHANGED, settings_panel.update_panel)
        self.event_handler.subscribe(EventType.INTERVAL_CHANGED, settings_panel.update_panel)
        self.event_handler.subscribe(EventType.RESAMPLE_RATE_CHANGED, settings_panel.update_panel)
        self.event_handler.subscribe(EventType.ATTRIBUTE_CHANGED, settings_panel.update_panel)
        main_layout.addWidget(settings_panel)

        # TABS

        tabs = QTabWidget(parent=self)

        # TAB 1 #
        original_df_tab = OriginalDfTab(self)
        self.event_handler.subscribe(EventType.DATAFRAME_CHANGED, original_df_tab.update_model)
        self.event_handler.subscribe(EventType.MASTER_SLAVES_CHANGED, original_df_tab.update_model)
        self.event_handler.subscribe(EventType.DIRECTION_CHANGED, original_df_tab.update_model)
        self.event_handler.subscribe(EventType.INTERVAL_CHANGED, original_df_tab.update_model)
        tabs.addTab(original_df_tab, "Original Dataframe")

        # TAB 2 #

        stats_tab = StatsTab(self)
        self.event_handler.subscribe(EventType.DATAFRAME_CHANGED, stats_tab.update_og_stats)

        self.event_handler.subscribe(EventType.DATAFRAME_CHANGED, stats_tab.update_work_stats)
        self.event_handler.subscribe(EventType.MASTER_SLAVES_CHANGED, stats_tab.update_work_stats)
        self.event_handler.subscribe(EventType.DIRECTION_CHANGED, stats_tab.update_work_stats)
        self.event_handler.subscribe(EventType.INTERVAL_CHANGED, stats_tab.update_work_stats)

        tabs.addTab(stats_tab, "General statistics")

        # TAB 3 #

        pair_plots_tab = PairPlotsTab(self)
        self.event_handler.subscribe(EventType.DATAFRAME_CHANGED, pair_plots_tab.update_plots)
        self.event_handler.subscribe(EventType.RESAMPLE_RATE_CHANGED, pair_plots_tab.update_plots)
        self.event_handler.subscribe(EventType.INTERVAL_CHANGED, pair_plots_tab.update_plots)
        tabs.addTab(pair_plots_tab, "Communication pairs")

        # TAB 4 #
        slave_plots_tab = SlavesPlotTab(self)
        self.event_handler.subscribe(EventType.DATAFRAME_CHANGED, slave_plots_tab.update_plots)
        self.event_handler.subscribe(EventType.MASTER_SLAVES_CHANGED, slave_plots_tab.update_plots)
        self.event_handler.subscribe(EventType.RESAMPLE_RATE_CHANGED, slave_plots_tab.update_plots)
        self.event_handler.subscribe(EventType.DIRECTION_CHANGED, slave_plots_tab.update_plots)
        self.event_handler.subscribe(EventType.INTERVAL_CHANGED, slave_plots_tab.update_plots)
        tabs.addTab(slave_plots_tab, "Slave communication")

        # TAB 5 #
        time_frame_view_tab = TimeFrameViewTab(self)
        self.event_handler.subscribe(EventType.DATAFRAME_CHANGED, time_frame_view_tab.update_model)
        self.event_handler.subscribe(EventType.MASTER_SLAVES_CHANGED, time_frame_view_tab.update_model)
        self.event_handler.subscribe(EventType.DIRECTION_CHANGED, time_frame_view_tab.update_model)
        self.event_handler.subscribe(EventType.INTERVAL_CHANGED, time_frame_view_tab.update_model)
        self.event_handler.subscribe(EventType.RESAMPLE_RATE_CHANGED, time_frame_view_tab.update_model)
        self.event_handler.subscribe(EventType.ATTRIBUTE_CHANGED, time_frame_view_tab.update_model)
        tabs.addTab(time_frame_view_tab, "Time frame view")

        # TAB 6 #
        attribute_stats_tab = AttributeStatsTab(self)
        self.event_handler.subscribe(EventType.DATAFRAME_CHANGED, attribute_stats_tab.update_tab)
        self.event_handler.subscribe(EventType.MASTER_SLAVES_CHANGED, attribute_stats_tab.update_tab)
        self.event_handler.subscribe(EventType.DIRECTION_CHANGED, attribute_stats_tab.update_tab)
        self.event_handler.subscribe(EventType.RESAMPLE_RATE_CHANGED, attribute_stats_tab.update_tab)
        self.event_handler.subscribe(EventType.RESAMPLE_RATE_CHANGED, attribute_stats_tab.update_tab)
        self.event_handler.subscribe(EventType.ATTRIBUTE_CHANGED, attribute_stats_tab.update_tab)
        tabs.addTab(attribute_stats_tab, "Attribute stats")

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
        """
        if self.df_working is not None:
            filtered_pair_ids = dsa.get_connected_pairs(self.master_station_id, self.slave_station_ids, self.pair_ids)

            filtered_direction_ids = dsa.get_direction_ids_by_filter(
                self.master_station_id, self.slave_station_ids, self.direction, self.direction_ids
            )

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
            self.df_working = pd.read_pickle("../save/df.pkl")

            self.preprocess_df()

            self.event_handler.notify(EventType.DATAFRAME_CHANGED, self.event_data)

            return

        file_path, _ = QFileDialog.getOpenFileName(parent=self, caption="Open file", filter="CSV files (*.csv *.txt)")

        if file_path:
            self.file_path = file_path
            dialog = OpenCsvWizard(file_path)
            if dialog.exec():
                # TODO exception
                dialect, dtype, self.fcn = dialog.get_csv_settings()
                try:
                    self.df_working = dsl.load_data(file_path, dtype, dialect)
                except ValueError as e:
                    dlg = QMessageBox(self)
                    dlg.setWindowTitle("Error")
                    dlg.setText(str(e))
                    dlg.setIcon(QMessageBox.Icon.Warning)
                    dlg.exec()
                    return

                self.df_working.to_pickle("../save/df3.pkl")  # TODO delete

                self.preprocess_df()

                self.event_handler.notify(EventType.DATAFRAME_CHANGED, self.event_data)

                # # TODO delete
                import pickle

                with open("../save/fcn.pkl", "wb") as f:
                    pickle.dump(self.fcn, f)

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
            LoadWarningMessageBox(self).exec()

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
            LoadWarningMessageBox(self).exec()

    def change_direction(self) -> None:
        if self.df_working is not None:
            dlg = ChangeDirectionDialog(og_direction=self.direction, parent=self)

            if dlg.exec():
                self.direction = dlg.get_direction()

                self.event_handler.notify(EventType.DIRECTION_CHANGED, self.event_data)
        else:
            LoadWarningMessageBox(self).exec()

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
            LoadWarningMessageBox(self).exec()

    def change_resample_rate(self) -> None:

        if self.df_working is not None:
            dlg = ChangeResampleRateDialog(self.resample_rate, parent=self)
            if dlg.exec():
                self.resample_rate = dlg.get_resample_rate()

                self.event_handler.notify(EventType.RESAMPLE_RATE_CHANGED, self.event_data)
        else:
            LoadWarningMessageBox(self).exec()

    def change_attribute_name(self) -> None:

        if self.df_working is not None:
            filtered_attributes = list(set(self.og_cols) - set(self.fcn.predefined_cols))
            dlg = SelectAttributeDialog(self.attribute_name, filtered_attributes, parent=self)
            if dlg.exec():
                self.attribute_name = dlg.get_attribute_name()

                self.event_handler.notify(EventType.ATTRIBUTE_CHANGED, self.event_data)
        else:
            LoadWarningMessageBox(self).exec()

    # endregion

    # region Utilities

    def preprocess_df(self) -> None:
        """Prepare the dataframe for further use in the app.

        Also create or update attributes used in the rest of the code of the app.
        """
        self.og_cols = self.df_working.columns

        self.direction = DirectionEnum.BOTH
        self.attribute_name = None
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

        # CHANGE DIRECTION #
        name = "Change direction"
        actions[name] = QAction(icon=QIcon("gui/icons/computa.png"), text=name, parent=self)
        actions[name].triggered.connect(self.change_direction)

        # CHANGE INTERVAL #
        name = "Change interval"
        actions[name] = QAction(icon=QIcon("gui/icons/computa.png"), text=name, parent=self)
        actions[name].triggered.connect(self.change_interval)

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
