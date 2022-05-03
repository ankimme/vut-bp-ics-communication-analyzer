# TODO doc

import pandas as pd

from matplotlib.backends.backend_qtagg import NavigationToolbar2QT

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QTableView


from gui.utils import DataFrameModel, EventData
from dsmanipulator import dsanalyzer as dsa
from gui.components import MplCanvas


class SlavesPlotTab(QWidget):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: white;")

        layout = QVBoxLayout()

        # self.canvas = MplCanvas(width=5, height=5, dpi=100, parent=self)
        self.canvas = MplCanvas(width=6, height=4.5, dpi=100, parent=self)
        toolbar = NavigationToolbar2QT(self.canvas, self)

        layout.addWidget(toolbar)
        layout.addWidget(self.canvas)

        # TABLE DATA
        self.stats_table = QTableView()
        self.stats_table.setSortingEnabled(True)
        self.stats_table.setAlternatingRowColors(True)
        self.stats_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        layout.addWidget(self.stats_table)

        self.setLayout(layout)

    def update_tab(self, data: EventData) -> None:
        self.update_plot(data)
        self.update_table_data(data)
        self.update()

    def update_plot(self, data: EventData) -> None:

        self.canvas.axes.cla()

        if len(data.df_filtered.index) > 0:
            # compute xlimits of axes
            # datetime_index = pd.DatetimeIndex(data.df_working[data.fcn.timestamp])
            # left_xlim = min(datetime_index)
            # right_xlim = max(datetime_index)

            # self.canvas.axes.set_xlim([left_xlim, right_xlim])
            self.canvas.axes.set_xlim([data.start_dt, data.end_dt])
            dsa.plot_slaves(
                data.df_filtered,
                data.fcn,
                self.canvas.axes,
                data.resample_rate,
                data.master_station_id,
                data.station_ids,
                data.pair_ids,
            )

        self.canvas.draw()

    def update_table_data(self, data: EventData) -> None:
        x = dsa.get_slaves_stats(
            data.df_filtered, data.fcn, data.master_station_id, data.slave_station_ids, data.station_ids, data.pair_ids
        )
        self.stats_table.setModel(DataFrameModel(x))
        self.stats_table.resizeColumnsToContents()
