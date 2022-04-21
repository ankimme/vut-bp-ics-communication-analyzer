from PyQt6.QtWidgets import QWidget, QMessageBox


class WarningMessageBox(QMessageBox):
    def __init__(self, message: str, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Warning")
        self.setText(message)
        self.setIcon(QMessageBox.Icon.Warning)
