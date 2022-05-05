"""TODO

Author
------
Andrea Chimenti

Date
----
March 2022
"""

from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg

from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QGridLayout

from dsmanipulator.dataobjects import DirectionEnum

from gui.eventhandler import EventData


class InfoLabel(QLabel):
    """A label showing formatted information.

    Format
    ------
    Property: Value
    """

    def __init__(self, property: str, parent: QWidget = None):
        """Init InfoLabel class with empty value.

        Parameters
        ----------
        property : str
            Property name.
        parent : QWidget, optional
            Parent.
        """
        super().__init__(parent)
        self._property = property

        self.set_value("")

    def set_value(self, new_value: str | int | float):
        """Set value of label without changing property.

        Parameters
        ----------
        new_value : str | int | float
            A new value the label will display.
        """
        if type(new_value) == float:
            self.setText(f"{self._property}: {new_value:.3f}")
        else:
            self.setText(f"{self._property}: {new_value}")


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=300) -> None:
        fig = Figure(figsize=(width, height), dpi=dpi)
        fig.set_tight_layout(True)

        super().__init__(fig)

        self.axes = fig.add_subplot(111)
        self.setParent(parent)


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
        self.stat_widgets["Attribute"].set_value(
            f"{data.attribute_name} ({len(data.attribute_values)} values selected)"
        )
        self.stat_widgets["Direction"].set_value(direction)
        self.stat_widgets["Interval"].set_value(f"{ds} -- {de}")
