# TODO doc

import pandas as pd
from bidict import bidict


from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout
from PyQt6.QtGui import QAction

from gui.utils import EventData
from gui.components import InfoLabel
from dsmanipulator import dsanalyzer as dsa
from gui.components import MplCanvas


class SlavesPlotTab(QWidget):
    def __init__(self, change_master_station_action: QAction, parent: QWidget = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout()

        # master staion label and change button
        self.master_station_label = InfoLabel("Master station", self)
        layout.addWidget(self.master_station_label)
        # TODO not sure whether to uncomment
        # change_master_station_button = QPushButton("Change")
        # change_master_station_button.setFixedWidth(100)
        # change_master_station_button.clicked.connect(change_master_station_action.trigger)
        # layout.addWidget(change_master_station_button)

        # resample rate label
        self.resample_rate_label = InfoLabel("Resample rate", self)
        layout.addWidget(self.resample_rate_label)

        self.canvas = MplCanvas(width=5, height=5, dpi=100, parent=self)
        layout.addWidget(self.canvas)

        layout.addStretch(1)

        self.setLayout(layout)

    def update_plots(self, data: EventData) -> None:
        assert all(col in data.df.columns for col in [data.fcn.timestamp, data.fcn.pair_id])

        self.master_station_label.set_value(data.station_ids[data.master_station_id])
        self.resample_rate_label.set_value(data.resample_rate)

        pair_combinations: list[frozenset] = []
        for slave_station_id in data.slave_station_ids:
            pair_combinations.append(frozenset({data.master_station_id, slave_station_id}))

        # filter pair_ids so that only pairs containing the master station are present
        filtered_pair_ids: bidict[int, frozenset] = bidict(
            {
                pair_id: pair_set
                for pair_id, pair_set in data.pair_ids.items()
                if data.master_station_id in pair_set and any(x for x in pair_combinations if x == pair_set)
            }
        )

        self.canvas.axes.cla()

        if filtered_pair_ids:
            tmpdf = data.df[data.df[data.fcn.pair_id].isin(filtered_pair_ids.keys())]

            # compute xlimits of axes
            datetime_index = pd.DatetimeIndex(tmpdf[data.fcn.timestamp])
            left_xlim = min(datetime_index)
            right_xlim = max(datetime_index)

            self.canvas.axes.set_xlim([left_xlim, right_xlim])
            dsa.plot_slaves(tmpdf, data.fcn, self.canvas.axes, data.station_ids, data.direction_ids, data.resample_rate)

        self.canvas.draw()
        self.update()
