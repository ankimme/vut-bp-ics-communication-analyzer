from PyQt6.QtWidgets import QWidget, QVBoxLayout
from gui.components import MplCanvas
from gui.utils import EventData
from dsmanipulator import dscreator as dsc
from dsmanipulator import dsanalyzer as dsa


class AttributeStatsTab(QWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        layout = QVBoxLayout()

        self.canvas = MplCanvas(width=5, height=5, dpi=100, parent=self)
        layout.addWidget(self.canvas)

        # layout.addStretch(1)

        self.setLayout(layout)

    def update_plots(self, data: EventData) -> None:
        # return
        # TODO assert
        if data.attribute_name:

            self.canvas.axes.cla()
            if len(data.filtered_df.index) == 0:
                return

            dsa.plot_attribute_values(
                data.filtered_df, data.fcn, self.canvas.axes, data.attribute_name, data.resample_rate
            )

            self.canvas.draw()
            self.update()
