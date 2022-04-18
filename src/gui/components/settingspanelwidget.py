"""A simple infopanel that shows user settings.

Author
------
Andrea Chimenti

Date
----
April 2022
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QGridLayout

from gui.components import InfoLabel
from gui.utils import EventData
from dsmanipulator.utils import DirectionEnum


class SettingsPanelWidget(QWidget):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.grid_layout = QGridLayout()

        self.stat_widgets: dict[str, InfoLabel] = {}
        setting_names = ["Master Station", "Slaves count", "Resample rate", "Attribute", "Direction", "Interval"]

        for setting in setting_names:
            setting_label = InfoLabel(setting)
            self.stat_widgets[setting] = setting_label

        self.grid_layout.addWidget(self.stat_widgets["Master Station"], 0, 0, Qt.AlignmentFlag.AlignLeft)
        self.grid_layout.addWidget(self.stat_widgets["Slaves count"], 0, 1, Qt.AlignmentFlag.AlignLeft)
        self.grid_layout.addWidget(self.stat_widgets["Resample rate"], 0, 2, Qt.AlignmentFlag.AlignLeft)
        self.grid_layout.addWidget(self.stat_widgets["Attribute"], 1, 0, Qt.AlignmentFlag.AlignLeft)
        self.grid_layout.addWidget(self.stat_widgets["Direction"], 1, 1, Qt.AlignmentFlag.AlignLeft)
        self.grid_layout.addWidget(self.stat_widgets["Interval"], 1, 2, Qt.AlignmentFlag.AlignLeft)

        self.setLayout(self.grid_layout)

    def update_panel(self, data: EventData) -> None:
        """Update values of infopanel shown to user.

        Parameters
        ----------
        data : EventData
            Data of update event.
        """
        match data.direction:
            case DirectionEnum.BOTH:
                direction = "Both"
            case DirectionEnum.M2S:
                direction = "Master to slave"
            case DirectionEnum.S2M:
                direction = "Slave to master"

        ds = data.start_dt.strftime("%d %h %H:%M:%S.%f")[:-4]
        de = data.end_dt.strftime("%d %h %H:%M:%S.%f")[:-4]

        self.stat_widgets["Master Station"].set_value(str(data.station_ids[data.master_station_id]))
        self.stat_widgets["Slaves count"].set_value(len(data.slave_station_ids))
        self.stat_widgets["Resample rate"].set_value(str(data.resample_rate))
        self.stat_widgets["Attribute"].set_value(data.attribute_name)
        self.stat_widgets["Direction"].set_value(direction)
        self.stat_widgets["Interval"].set_value(f"{ds} -- {de}")
