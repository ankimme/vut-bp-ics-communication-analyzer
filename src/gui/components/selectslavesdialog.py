"""Dialog used to select slave stations of interest.

Author
------
Andrea Chimenti

Date
----
March 2022
"""

from bidict import bidict

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QWidget, QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox, QPushButton

from dsmanipulator import dsanalyzer as dsa
from dsmanipulator.utils import Station


class SelectSlavesDialog(QDialog):
    """Select slaves dialog.

    Attributes
    ----------
    layout : QVBoxLayout
        Main dialog layout.
    boxes : dict[int, QCheckBox]
        Key : ID of station.
        Value : Assigned checkbox.
    buttons : QDialogButtonBox
        Dialog control buttons
    """

    def __init__(
        self,
        master_station_id: int,
        og_slave_station_ids: list[int],
        station_ids: bidict[int, Station],
        pair_ids: bidict[int, frozenset],
        parent: QWidget = None,
    ) -> None:
        """Initialize dialog.

        Parameters
        ----------
        master_station_id : int
            ID of master station.
        og_slave_station_ids : list[int]
           IDs of stations that will be preselected.
        station_ids : bidict[int, Station]
            Key : ID of station.
            Value : Station.
        pair_ids : bidict[int, frozenset]
            Key : ID of station.
            Value : Pair of station ids.
        parent : QWidget, optional
            Parent widget.
        """
        super().__init__(parent)

        self.setWindowTitle("Select slaves")

        self.layout = QVBoxLayout()

        # select all button
        select_all_button = QPushButton("Select all")
        select_all_button.clicked.connect(self.select_all)
        self.layout.addWidget(select_all_button)

        # deselect all button
        deselect_all_button = QPushButton("Deselect all")
        deselect_all_button.clicked.connect(self.deselect_all)
        self.layout.addWidget(deselect_all_button)

        # ids of stations that communicate with the master station
        all_slave_ids = dsa.get_connected_stations(pair_ids, master_station_id)

        self.boxes: dict[int, QCheckBox] = {}

        for station_id, station in station_ids.items():
            if station_id in all_slave_ids:
                box = QCheckBox(str(station), self)

                if station_id in og_slave_station_ids:
                    box.setChecked(True)

                self.boxes[station_id] = box
                self.layout.addWidget(box)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.layout.addWidget(self.buttons)
        self.setLayout(self.layout)

    @pyqtSlot()
    def select_all(self) -> None:
        """Check all buttons in dialog."""
        for box in self.boxes.values():
            box.setChecked(True)

    @pyqtSlot()
    def deselect_all(self) -> None:
        """Uncheck all buttons in dialog."""
        for box in self.boxes.values():
            box.setChecked(False)

    def get_slave_stations_ids(self) -> list[int]:
        """Return the ids of selected stations in dialog.

        Returns
        -------
        list[int]
            List of IDs of selected slave stations.
        """
        return [station_id for station_id, box in self.boxes.items() if box.isChecked()]
