"""Representation of a simple information label.

Author
------
Andrea Chimenti

Date
----
March 2022
"""

from PyQt6.QtWidgets import QWidget, QLabel


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
