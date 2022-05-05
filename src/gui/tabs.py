# TODO doc

import os
import numpy as np
import pandas as pd

from matplotlib.backends.backend_qtagg import NavigationToolbar2QT

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
    QTableView,
)
from PyQt6.QtGui import QFont

from dsmanipulator import dscreator as dsc
from dsmanipulator import dsanalyzer as dsa
from dsmanipulator.dataobjects import DirectionEnum

from gui.datamodels import DataFrameModel
from gui.eventhandler import EventData
from gui.widgets import MplCanvas, InfoLabel


class OriginalDfTab(QTableView):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.df_model: DataFrameModel

        self.setSortingEnabled(True)
        # self.horizontalHeader().setStretchLastSection(True)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

    def update_model(self, data: EventData) -> None:
        self.df_model = DataFrameModel(data.df_filtered.loc[:, data.df_og.columns])
        self.setModel(self.df_model)
        self.resizeColumnsToContents()
        self.update()


class StatsTab(QScrollArea):
    def __init__(self, parent: QWidget = None) -> None:
        """TODO

        Attributes
        ----------
        stat_widgets : dict[str, InfoLabel]
            Key : Statistic name.
            Value : Assigned label.
        """
        super().__init__(parent)

        self.setWidgetResizable(True)

        # self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        # self.setStyleSheet("background-color: white;")

        grid_layout = QGridLayout()
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)

        # ORIGINAL DATAFRAME #

        self.og_stat_widgets: dict[str, InfoLabel] = {}
        og_stat_names = [
            "Start time",
            "End time",
            "Time span",
            "Total packets",
            "Master to slave packets",
            "Slave to master packets",
            "IAT mean",
            "IAT median",
            "IAT min",
            "IAT max",
            "Pairs count",
            "File name",
            "Column count",
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
            "Total packets",
            "Master to slave packets",
            "Slave to master packets",
            "IAT mean",
            "IAT median",
            "IAT min",
            "IAT max",
            "Unique values of attributes",
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

        unique_values_dialog_scroll_area = QScrollArea()
        unique_values_dialog_scroll_area.setWidgetResizable(True)
        dialog_layout.addWidget(unique_values_dialog_scroll_area)

        q = QWidget()
        unique_values_dialog_scroll_area.setWidget(q)

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

        work_df_layout.insertLayout(11, button_hbox)

        work_df_layout.addStretch(1)

        # PUTTING IT TOGETHER #
        grid_layout.addWidget(QLabel("ORIGINAL DATAFRAME"), 0, 0)
        grid_layout.addWidget(QLabel("FILTERED DATAFRAME"), 0, 1)

        grid_layout.addLayout(og_df_layout, 1, 0)
        grid_layout.addLayout(work_df_layout, 1, 1)

        parent_widget = QWidget(self)
        parent_widget.setLayout(grid_layout)
        self.setWidget(parent_widget)

    def update_og_stats(self, data: EventData) -> None:
        total_packet_count = len(data.df_working.index)
        m2s_packet_count = dsa.get_packet_count_by_direction(
            data.df_working,
            data.fcn,
            data.master_station_id,
            data.slave_station_ids,
            data.direction_ids,
            DirectionEnum.M2S,
        )
        s2m_packet_count = dsa.get_packet_count_by_direction(
            data.df_working,
            data.fcn,
            data.master_station_id,
            data.slave_station_ids,
            data.direction_ids,
            DirectionEnum.S2M,
        )
        m2s_percentage = m2s_packet_count / total_packet_count * 100 if total_packet_count > 0 else 0
        s2m_percentage = s2m_packet_count / total_packet_count * 100 if total_packet_count > 0 else 0

        self.og_stat_widgets["Total packets"].set_value(total_packet_count)
        self.og_stat_widgets["Master to slave packets"].set_value(f"{m2s_packet_count} ({m2s_percentage:.2f}%)")
        self.og_stat_widgets["Slave to master packets"].set_value(f"{s2m_packet_count} ({s2m_percentage:.2f}%)")

        self.og_stat_widgets["File name"].set_value(os.path.basename(data.file_path))
        self.og_stat_widgets["Column count"].set_value(len(data.df_og.columns))
        self.og_stat_widgets["Start time"].set_value(
            data.df_og[data.fcn.timestamp].iloc[0].strftime("%d %h %Y %H:%M:%S.%f")[:-4]
        )
        self.og_stat_widgets["End time"].set_value(
            data.df_og[data.fcn.timestamp].iloc[-1].strftime("%d %h %Y %H:%M:%S.%f")[:-4]
        )
        self.og_stat_widgets["Time span"].set_value(dsa.get_df_time_span(data.df_working, data.fcn))
        self.og_stat_widgets["Pairs count"].set_value(len(data.pair_ids))

        s = "\n"
        for iat_mean, iat_median in data.df_og.dtypes.items():
            pad = 25 - len(iat_mean)
            filler = " "
            s += f"{iat_mean}{filler*pad}{iat_median}\n"

        self.og_stat_widgets["Column types"].set_value(s)

        if data.fcn.rel_time in data.df_working:
            iat_mean, iat_median, iat_min, iat_max = dsa.get_iat_stats_whole_df(data.df_working, data.fcn)
            self.og_stat_widgets["IAT mean"].set_value(iat_mean)
            self.og_stat_widgets["IAT median"].set_value(iat_median)
            self.og_stat_widgets["IAT min"].set_value(iat_min)
            self.og_stat_widgets["IAT max"].set_value(iat_max)
        else:
            self.og_stat_widgets["IAT mean"].set_value("Missing relative time")
            self.og_stat_widgets["IAT median"].set_value("Missing relative time")
            self.og_stat_widgets["IAT min"].set_value("Missing relative time")
            self.og_stat_widgets["IAT max"].set_value("Missing relative time")

    def update_work_stats(self, data: EventData) -> None:
        total_packet_count = len(data.df_filtered.index)
        m2s_packet_count = dsa.get_packet_count_by_direction(
            data.df_filtered,
            data.fcn,
            data.master_station_id,
            data.slave_station_ids,
            data.direction_ids,
            DirectionEnum.M2S,
        )
        s2m_packet_count = dsa.get_packet_count_by_direction(
            data.df_filtered,
            data.fcn,
            data.master_station_id,
            data.slave_station_ids,
            data.direction_ids,
            DirectionEnum.S2M,
        )
        m2s_percentage = m2s_packet_count / total_packet_count * 100 if total_packet_count > 0 else 0
        s2m_percentage = s2m_packet_count / total_packet_count * 100 if total_packet_count > 0 else 0
        self.work_stat_widgets["Total packets"].set_value(total_packet_count)
        self.work_stat_widgets["Master to slave packets"].set_value(f"{m2s_packet_count} ({m2s_percentage:.2f}%)")
        self.work_stat_widgets["Slave to master packets"].set_value(f"{s2m_packet_count} ({s2m_percentage:.2f}%)")

        for i in reversed(range(self.content_layout.count())):
            self.content_layout.itemAt(i).widget().setParent(None)

        attribute_cols = list(set(data.df_og.columns) - set(data.fcn.predefined_cols))
        s = "\n"
        for attribute in attribute_cols:
            pad = 25 - len(attribute)
            filler = " "
            unique_values = data.df_filtered[attribute].dropna().unique()
            s += f"{attribute}{filler*pad}{len(unique_values)}\n"

            label = QLabel()
            label.setText(
                f"<b>{attribute}</b><br>{'<br>'.join(f'{x:g}' if isinstance(x, np.floating) else str(x) for x in unique_values)}"
            )
            self.content_layout.addWidget(label)
        self.work_stat_widgets["Unique values of attributes"].set_value(s)
        self.unique_values_button.setEnabled(True)

        if len(data.df_filtered.index) > 0:
            self.work_stat_widgets["Start time"].set_value(
                data.df_filtered[data.fcn.timestamp].iloc[0].strftime("%d %h %Y %H:%M:%S.%f")[:-4]
            )
            self.work_stat_widgets["End time"].set_value(
                data.df_filtered[data.fcn.timestamp].iloc[-1].strftime("%d %h %Y %H:%M:%S.%f")[:-4]
            )
            self.work_stat_widgets["Time span"].set_value(dsa.get_df_time_span(data.df_filtered, data.fcn))

            if data.fcn.rel_time in data.df_filtered.columns:
                iat_mean, iat_median, iat_min, iat_max = dsa.get_iat_stats_filtered(
                    data.df_filtered, data.fcn, data.master_station_id, data.slave_station_ids, data.pair_ids
                )
                self.work_stat_widgets["IAT mean"].set_value(iat_mean)
                self.work_stat_widgets["IAT median"].set_value(iat_median)
                self.work_stat_widgets["IAT min"].set_value(iat_min)
                self.work_stat_widgets["IAT max"].set_value(iat_max)
            else:
                self.work_stat_widgets["IAT mean"].set_value("Missing relative time")
                self.work_stat_widgets["IAT median"].set_value("Missing relative time")
                self.work_stat_widgets["IAT min"].set_value("Missing relative time")
                self.work_stat_widgets["IAT max"].set_value("Missing relative time")
        else:
            self.work_stat_widgets["Start time"].set_value("")
            self.work_stat_widgets["End time"].set_value("")
            self.work_stat_widgets["Time span"].set_value("")
            self.work_stat_widgets["IAT mean"].set_value("")
            self.work_stat_widgets["IAT median"].set_value("")
            self.work_stat_widgets["IAT min"].set_value("")
            self.work_stat_widgets["IAT max"].set_value("")

    @pyqtSlot()
    def show_unique_values(self):
        self.unique_values_dialog.exec()


class PairPlotsTab(QScrollArea):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: white;")

        # QScrollArea -> QWidget -> layout -> content widgets
        self.parent_widget = QWidget(self)

        self.parent_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.parent_widget.setMaximumWidth(1200)

        self.plots_layout = QVBoxLayout(self.parent_widget)

        self.parent_widget.setLayout(self.plots_layout)

        self.setWidget(self.parent_widget)

    def update_plots(self, data: EventData) -> None:
        assert all(col in data.df_working.columns for col in [data.fcn.timestamp, data.fcn.pair_id])

        for i in reversed(range(self.plots_layout.count())):
            self.plots_layout.itemAt(i).widget().setParent(None)

        plots: list[MplCanvas] = []
        max_ylim = 0

        for pair_id, pair in data.pair_ids.items():
            plot = MplCanvas(parent=self.parent_widget, width=6, height=3.5, dpi=100)

            toolbar = NavigationToolbar2QT(plot, self)
            plot.axes.set_xlim([data.start_dt, data.end_dt])
            dsa.plot_pair_flow(
                data.df_working, data.fcn, plot.axes, pair_id, data.station_ids, data.direction_ids, data.resample_rate
            )

            plots.append(plot)
            max_ylim = max(max_ylim, plot.axes.get_ylim()[1])

            x, y = pair
            label = QLabel(f"Stations: {data.station_ids[x]} {data.station_ids[y]}")
            label.setFont(QFont("Monospace", 14))
            self.plots_layout.addWidget(label)

            self.plots_layout.addWidget(toolbar)
            self.plots_layout.addWidget(plot)

        # set y-axis to have the same scale for all plots
        for plot in plots:
            plot.axes.set_ylim([0, max_ylim])

        self.update()


class SlavesPlotTab(QWidget):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: white;")

        layout = QVBoxLayout()

        self.canvas = MplCanvas(width=6, height=4.5, dpi=100, parent=self)
        toolbar = NavigationToolbar2QT(self.canvas, self)

        layout.addWidget(toolbar)
        layout.addWidget(self.canvas)

        # TABLE DATA
        self.stats_table = QTableView()
        self.stats_table.setSortingEnabled(True)
        self.stats_table.setAlternatingRowColors(True)
        self.stats_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        layout.addWidget(self.stats_table)

        self.setLayout(layout)

    def update_tab(self, data: EventData) -> None:
        self.update_plot(data)
        self.update_table_data(data)
        self.update()

    def update_plot(self, data: EventData) -> None:

        self.canvas.axes.cla()

        if len(data.df_filtered.index) > 0:
            self.canvas.axes.set_xlim([data.start_dt, data.end_dt])
            dsa.plot_slaves(
                data.df_filtered,
                data.fcn,
                self.canvas.axes,
                data.resample_rate,
                data.master_station_id,
                data.station_ids,
                data.pair_ids,
            )

        self.canvas.draw()

    def update_table_data(self, data: EventData) -> None:
        x = dsa.get_slaves_stats(
            data.df_filtered, data.fcn, data.master_station_id, data.slave_station_ids, data.station_ids, data.pair_ids
        )
        self.stats_table.setModel(DataFrameModel(x))
        self.stats_table.resizeColumnsToContents()


class TimeFrameViewTab(QTableView):
    def __init__(self, parent: QWidget = None) -> None:
        """TODO

        Attributes
        ----------
        TODO

        """
        super().__init__(parent)

        self.df_model: DataFrameModel

        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

    def update_model(self, data: EventData) -> None:
        if data.attribute_name is not None:
            tmpdf = data.df_filtered.loc[:, [data.fcn.timestamp, data.attribute_name]]

            tmpdf = dsc.convert_to_timeseries(tmpdf, data.fcn)
            tmpdf = dsc.expand_values_to_columns(tmpdf, data.attribute_name)
            tmpdf = tmpdf.resample(data.resample_rate).sum()
            tmpdf = tmpdf.rename(columns={og: og.lstrip(f"{data.attribute_name}:") for og in tmpdf.columns})

            tmpdf.reset_index(inplace=True)

            self.df_model = DataFrameModel(tmpdf)
            self.setModel(self.df_model)
            self.resizeColumnsToContents()

        else:
            self.setModel(DataFrameModel(pd.DataFrame()))

        self.update()


class AttributeStatsTab(QWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        layout = QVBoxLayout()

        # CANVA
        self.canvas = MplCanvas(width=6, height=4.5, dpi=100, parent=self)
        toolbar = NavigationToolbar2QT(self.canvas, self)

        layout.addWidget(toolbar)
        layout.addWidget(self.canvas)

        # TABLE DATA
        self.attribute_stats_table = QTableView()
        self.attribute_stats_table.setSortingEnabled(True)
        self.attribute_stats_table.setAlternatingRowColors(True)
        self.attribute_stats_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        layout.addWidget(self.attribute_stats_table)

        self.setLayout(layout)

    def update_tab(self, data: EventData) -> None:
        self.update_plot(data)
        self.update_table_data(data)
        self.update()

    def update_plot(self, data: EventData) -> None:
        # return
        # TODO assert
        self.canvas.axes.cla()
        if data.attribute_name is not None:

            if len(data.df_filtered.index) > 0 and len(data.attribute_values) > 0:

                dsa.plot_attribute_values(
                    data.df_filtered[data.df_filtered[data.attribute_name].isin(data.attribute_values)],
                    data.fcn,
                    data.attribute_name,
                    data.resample_rate,
                    self.canvas.axes,
                )

        self.canvas.draw()

    def update_table_data(self, data: EventData) -> None:
        if data.attribute_name is not None:
            x = dsa.get_attribute_stats(
                data.df_filtered,
                data.fcn,
                data.attribute_name,
                data.resample_rate,
            )
            self.attribute_stats_table.setModel(DataFrameModel(x))
            self.attribute_stats_table.resizeColumnsToContents()
        else:
            self.attribute_stats_table.setModel(DataFrameModel(pd.DataFrame()))
