# todo doc

from PyQt6.QtWidgets import QWidget, QVBoxLayout


class TimeFrameViewTab(QWidget):
    def __init__(self, parent: QWidget = None) -> None:
        """TODO

        Attributes
        ----------
        stat_widgets : dict[str, InfoLabel]
            Key : Statistic name.
            Value : Assigned label.
        """
        super().__init__(parent)

        vbox_layout = QVBoxLayout(self)
        self.layout(vbox_layout)
