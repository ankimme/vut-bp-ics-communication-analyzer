# TODO doc

from bidict import bidict
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QDialog, QVBoxLayout, QButtonGroup, QDialogButtonBox, QRadioButton

from dsmanipulator.utils import Station


class SelectMasterStationsDialog(QDialog):
    """A simple dialog used for selecting the master station."""

    def __init__(self, station_ids: bidict[int, Station], master_station_id: int = None, parent: QWidget = None):
        """Initialize the dialog window.

        Parameters
        ----------
        station_ids : bidict[int, Station]
            Key : ID of station.
            Value : Station.
        master_station_id : int, optional
            Id of current master station.
        """
        super().__init__(parent)

        self.setWindowTitle("Select master station")

        self.layout = QVBoxLayout()

        self.button_group = QButtonGroup(self)

        for station_id, station in station_ids.items():
            button = QRadioButton(str(station))
            if station_id == master_station_id:
                button.setChecked(True)
            self.button_group.addButton(button, id=station_id)
            self.layout.addWidget(button, Qt.AlignmentFlag.AlignCenter)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.layout.addWidget(self.buttons)
        self.setLayout(self.layout)

    def get_master_station_id(self) -> int:
        """Return the id of the selected station in dialog.

        Returns
        -------
        int
            ID of master station.
        """
        return self.button_group.checkedId()
