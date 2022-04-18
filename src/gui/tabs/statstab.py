# TODO doc

import os
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QDialog,
    QScrollArea,
)

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

        grid_layout = QGridLayout()
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)

        # ORIGINAL DATAFRAME #

        self.og_stat_widgets: dict[str, InfoLabel] = {}
        og_stat_names = [
            "Start time",
            "End time",
            "Time span",
            "Row count",
            "File name",
            "Column count",
            "Pairs count",
            "Column types",
        ]

        og_df_layout = QVBoxLayout()

        for stat in og_stat_names:
            stat_label = InfoLabel(stat)
            self.og_stat_widgets[stat] = stat_label
            og_df_layout.addWidget(stat_label)

        self.og_stat_widgets["Column types"].setWordWrap(True)

        og_df_layout.addStretch(1)

        # WORK DATAFRAME #

        self.work_stat_widgets: dict[str, InfoLabel] = {}
        work_stat_names = [
            "Start time",
            "End time",
            "Time span",
            "Row count",
            "Unique values",
        ]

        work_df_layout = QVBoxLayout()

        for stat in work_stat_names:
            stat_label = InfoLabel(stat)
            self.work_stat_widgets[stat] = stat_label
            work_df_layout.addWidget(stat_label)

        # UNIQUE VALUES DIALOG #

        # QDialog -> layout -> QScrollArea -> QWidget -> layout -> content widgets

        self.unique_values_dialog = QDialog()
        self.unique_values_dialog.setWindowTitle("Unique values of attributes")
        flags = self.unique_values_dialog.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint
        self.unique_values_dialog.setWindowFlags(flags)

        dialog_layout = QVBoxLayout()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        dialog_layout.addWidget(scroll_area)

        q = QWidget()
        scroll_area.setWidget(q)

        self.content_layout = QVBoxLayout()
        q.setLayout(self.content_layout)

        self.unique_values_dialog.setLayout(dialog_layout)

        # UNIQUE VALUES BUTTON #

        self.unique_values_button = QPushButton("Detailed view", self)
        self.unique_values_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.unique_values_button.resize(120, 50)
        self.unique_values_button.setEnabled(False)
        self.unique_values_button.clicked.connect(self.show_unique_values)

        button_hbox = QHBoxLayout()
        button_hbox.addWidget(self.unique_values_button)
        button_hbox.addStretch(1)

        work_df_layout.insertLayout(5, button_hbox)

        work_df_layout.addStretch(1)

        # PUTTING IT TOGETHER #
        grid_layout.addWidget(QLabel("ORIGINAL DATAFRAME"), 0, 0)
        grid_layout.addWidget(QLabel("FILTERED DATAFRAME"), 0, 1)

        grid_layout.addLayout(og_df_layout, 1, 0)
        grid_layout.addLayout(work_df_layout, 1, 1)

        self.setLayout(grid_layout)

    def update_og_stats(self, data: EventData) -> None:
        self.og_stat_widgets["File name"].set_value(os.path.basename(data.file_path))
        self.og_stat_widgets["Row count"].set_value(len(data.df_og.index))
        self.og_stat_widgets["Column count"].set_value(len(data.df_og.columns))
        self.og_stat_widgets["Start time"].set_value(
            data.df_og[data.fcn.timestamp].iloc[0].strftime("%d %h %Y %H:%M:%S.%f")[:-4]
        )
        self.og_stat_widgets["End time"].set_value(
            data.df_og[data.fcn.timestamp].iloc[-1].strftime("%d %h %Y %H:%M:%S.%f")[:-4]
        )
        self.og_stat_widgets["Time span"].set_value(dsa.get_df_time_span(data.df_og, data.fcn))
        self.og_stat_widgets["Pairs count"].set_value(len(data.pair_ids))

        s = "\n"
        for a, b in data.df_og.dtypes.items():
            pad = 25 - len(a)
            filler = " "
            s += f"{a}{filler*pad}{b}\n"

        self.og_stat_widgets["Column types"].set_value(s)

    def update_work_stats(self, data: EventData) -> None:
        self.work_stat_widgets["Row count"].set_value(len(data.df_filtered.index))

        for i in reversed(range(self.content_layout.count())):
            self.content_layout.itemAt(i).widget().setParent(None)

        attribute_cols = list(set(data.df_og.columns) - set(data.fcn.predefined_cols))
        s = "\n"
        for attribute in attribute_cols:
            pad = 25 - len(attribute)
            filler = " "
            unique_values = data.df_filtered[attribute].unique()
            s += f"{attribute}{filler*pad}{len(unique_values)}\n"

            label = QLabel()
            label.setText(f"<b>{attribute}</b><br>{'<br>'.join(str(x) for x in unique_values)}")
            self.content_layout.addWidget(label)
        self.work_stat_widgets["Unique values"].set_value(s)
        self.unique_values_button.setEnabled(True)

        if len(data.df_filtered.index) > 0:
            self.work_stat_widgets["Start time"].set_value(
                data.df_filtered[data.fcn.timestamp].iloc[0].strftime("%d %h %Y %H:%M:%S.%f")[:-4]
            )
            self.work_stat_widgets["End time"].set_value(
                data.df_filtered[data.fcn.timestamp].iloc[-1].strftime("%d %h %Y %H:%M:%S.%f")[:-4]
            )
            self.work_stat_widgets["Time span"].set_value(dsa.get_df_time_span(data.df_filtered, data.fcn))
        else:
            self.work_stat_widgets["Start time"].set_value("")
            self.work_stat_widgets["End time"].set_value("")
            self.work_stat_widgets["Time span"].set_value("")

    @pyqtSlot()
    def show_unique_values(self):
        self.unique_values_dialog.exec()
