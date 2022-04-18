"""Representation of a tab showing communication intensity for each pair.

Author
------
Andrea Chimenti

Date
----
March 2022
"""


from matplotlib.backends.backend_qtagg import NavigationToolbar2QT

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget, QScrollArea, QVBoxLayout, QSizePolicy, QLabel

from dsmanipulator import dsanalyzer as dsa

from gui.utils import EventData
from gui.components import MplCanvas


class PairPlotsTab(QScrollArea):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: white;")

        # QScrollArea -> QWidget -> layout -> content widgets
        self.parent_widget = QWidget(self)

        self.parent_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.parent_widget.setMaximumWidth(1200)

        self.plots_layout = QVBoxLayout(self.parent_widget)

        self.parent_widget.setLayout(self.plots_layout)

        self.setWidget(self.parent_widget)

    def update_plots(self, data: EventData) -> None:
        assert all(col in data.df_working.columns for col in [data.fcn.timestamp, data.fcn.pair_id])

        for i in reversed(range(self.plots_layout.count())):
            self.plots_layout.itemAt(i).widget().setParent(None)

        plots: list[MplCanvas] = []
        max_ylim = 0

        for pair_id, pair in data.pair_ids.items():
            plot = MplCanvas(parent=self.parent_widget, width=6, height=3.5, dpi=100)

            toolbar = NavigationToolbar2QT(plot, self)
            # plot.axes.set_xlim([left_xlim, right_xlim])
            plot.axes.set_xlim([data.start_dt, data.end_dt])
            dsa.plot_pair_flow(
                data.df_working, data.fcn, plot.axes, pair_id, data.station_ids, data.direction_ids, data.resample_rate
            )

            plots.append(plot)
            max_ylim = max(max_ylim, plot.axes.get_ylim()[1])

            x, y = pair
            label = QLabel(f"Stations: {data.station_ids[x]} {data.station_ids[y]}")
            label.setFont(QFont("Monospace", 14))
            self.plots_layout.addWidget(label)

            self.plots_layout.addWidget(toolbar)
            self.plots_layout.addWidget(plot)

        # set y-axis to have the same scale for all plots
        for plot in plots:
            plot.axes.set_ylim([0, max_ylim])

        self.update()

    # def update_master_station(self, data: EventData) -> None:
    #     self.master_station_label.set_value(data.station_ids[data.master_station_id])
