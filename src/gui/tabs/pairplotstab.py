"""Representation of a tab showing communication intensity for each pair.

Author
------
Andrea Chimenti

Date
----
March 2022
"""

import pandas as pd

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QScrollArea, QVBoxLayout, QSizePolicy, QLabel

from dsmanipulator import dsanalyzer as dsa

from gui.utils import EventData
from gui.components import InfoLabel
from gui.components import MplCanvas


class PairPlotsTab(QScrollArea):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.master_station_label: InfoLabel

    def update_plots(self, data: EventData) -> None:
        # TODO rearrange to init
        assert all(col in data.df.columns for col in [data.fcn.timestamp, data.fcn.pair_id])

        parent_widget = QWidget(self)

        parent_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        vbox_layout = QVBoxLayout(parent_widget)

        self.master_station_label = InfoLabel("Master station")
        self.master_station_label.set_value(data.station_ids[data.master_station_id])
        vbox_layout.addWidget(self.master_station_label)

        # compute xlimits of axes
        datetime_index = pd.DatetimeIndex(data.df[data.fcn.timestamp])
        left_xlim = min(datetime_index)
        right_xlim = max(datetime_index)

        for pair_id, pair in data.pair_ids.items():
            plot = MplCanvas(parent=parent_widget, width=7, height=3.5, dpi=100)
            plot.axes.set_xlim([left_xlim, right_xlim])
            dsa.plot_pair_flow(data.df, data.fcn, plot.axes, pair_id, data.station_ids, data.direction_ids)

            l1 = QLabel(f"Stations")
            x, y = pair
            l2 = QLabel(str(data.station_ids[x]))
            l3 = QLabel(str(data.station_ids[y]))
            vbox_layout.addWidget(l1)
            vbox_layout.addWidget(l2)
            vbox_layout.addWidget(l3)

            vbox_layout.addWidget(plot)
        parent_widget.setLayout(vbox_layout)

        self.setWidget(parent_widget)
        self.update()

    def update_master_station(self, data: EventData) -> None:
        self.master_station_label.set_value(data.station_ids[data.master_station_id])
