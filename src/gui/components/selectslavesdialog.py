# TODO doc

from bidict import bidict
from PyQt6.QtWidgets import QWidget, QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox
from dsmanipulator.utils import Station


class SelectSlavesDialog(QDialog):
    def __init__(self, master_station_id: int, station_ids: bidict[int, Station], pair_ids: bidict[int, frozenset], parent: QWidget = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Select slaves")

        self.layout = QVBoxLayout()

        # ids of stations that communicate with the master station
        slave_ids = set()
        for pair in pair_ids.values():
            if master_station_id in pair:
                x, y = pair
                slave_ids.add(x)
                slave_ids.add(y)
        slave_ids.discard(master_station_id)

        self.boxes: dict[int, QCheckBox] = {}

        for station_id, station in station_ids.items():
            if station_id in slave_ids:
                box = QCheckBox(str(station), self)
                self.boxes[station_id] = box
                self.layout.addWidget(box)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.layout.addWidget(self.buttons)
        self.setLayout(self.layout)

    def get_slave_stations_ids(self) -> list[int]:
        """Return the ids of selected stations in dialog.

        Returns
        -------
        list[int]
            List of IDs of slave stations.
        """
        return [station_id for station_id, box in self.boxes.items() if box.isChecked()]
