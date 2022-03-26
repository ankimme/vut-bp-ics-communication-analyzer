import pandas as pd
from bidict import bidict

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QScrollArea, QSizePolicy, QVBoxLayout

from gui.utils import EventData
from gui.components import InfoLabel
from dsmanipulator import dsanalyzer as dsa
from gui.components import MplCanvas


class SlavesPlotTab(QScrollArea):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        parent_widget = QWidget(self)

        parent_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        vbox_layout = QVBoxLayout(parent_widget)

        self.master_station_label = InfoLabel("Master station")
        vbox_layout.addWidget(self.master_station_label)

        self.plot = MplCanvas(parent=parent_widget, width=10, height=6, dpi=100)
        vbox_layout.addWidget(self.plot)

        parent_widget.setLayout(vbox_layout)

        self.setWidget(parent_widget)

    def update_plots(self, data: EventData) -> None:

        assert all(col in data.df.columns for col in [data.fcn.timestamp, data.fcn.pair_id])

        self.master_station_label.set_value(data.station_ids[data.master_station_id])

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

        # TODO
        if not filtered_pair_ids:
            return

        tmpdf = data.df[data.df[data.fcn.pair_id].isin(filtered_pair_ids.keys())]

        # compute xlimits of axes
        datetime_index = pd.DatetimeIndex(tmpdf[data.fcn.timestamp])
        left_xlim = min(datetime_index)
        right_xlim = max(datetime_index)

        self.plot.axes.set_xlim([left_xlim, right_xlim])
        dsa.plot_slaves(tmpdf, data.fcn, self.plot.axes, data.station_ids, data.direction_ids)
        self.plot.draw()

        self.update()

    def update_master_station(self, data: EventData) -> None:
        self.master_station_label.set_value(data.station_ids[data.master_station_id])

    # def update_slave_stations(self, data: EventData) -> None:
    #     pass
