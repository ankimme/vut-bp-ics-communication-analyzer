# TODO doc

import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout

from dsmanipulator import dsanalyzer as dsa
from gui.components import InfoLabel
from gui.utils import EventData


class StatsTab(QWidget):
    def __init__(self, parent: QWidget = None) -> None:
        """TODO

        Attributes
        ----------
        stat_widgets : dict[str, InfoLabel]
            Key : Statistic name.
            Value : Assigned label.
        """
        super().__init__(parent)

        self.stat_widgets: dict[str, InfoLabel] = {}
        stat_names = ["File name", "Row count", "Column count", "Time span", "Pairs count", "Master station"]

        layout = QVBoxLayout()

        for stat in stat_names:
            stat_label = InfoLabel(stat)
            self.stat_widgets[stat] = stat_label
            layout.addWidget(stat_label)

        self.setLayout(layout)

    def update_stats(self, data: EventData) -> None:
        assert data.file_path

        self.stat_widgets["File name"].set_value(os.path.basename(data.file_path))
        self.stat_widgets["Row count"].set_value(len(data.df.index))
        self.stat_widgets["Column count"].set_value(len(data.df.columns))
        self.stat_widgets["Time span"].set_value(dsa.compute_time_span(data.df, data.fcn))
        self.stat_widgets["Pairs count"].set_value(len(data.pair_ids))
        self.stat_widgets["Master station"].set_value(str(data.station_ids[data.master_station_id]))

    def update_master_station(self, data: EventData) -> None:
        self.stat_widgets["Master station"].set_value(str(data.station_ids[data.master_station_id]))
