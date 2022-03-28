# TODO doc

import pandas as pd
from bidict import bidict


from PyQt6.QtWidgets import QWidget, QVBoxLayout
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

        self.canvas.axes.cla()

        if len(data.filtered_df.index) > 0:
            # compute xlimits of axes
            datetime_index = pd.DatetimeIndex(data.df[data.fcn.timestamp])
            left_xlim = min(datetime_index)
            right_xlim = max(datetime_index)

            self.canvas.axes.set_xlim([left_xlim, right_xlim])
            dsa.plot_slaves(data.filtered_df, data.fcn, self.canvas.axes, data.resample_rate)

        self.canvas.draw()
        self.update()
