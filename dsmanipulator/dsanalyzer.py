import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, AutoDateLocator
from matplotlib.axes import Axes
import pandas as pd

from . import dscreator as dsc
from .utils.dataobjects import FileColumnNames


# region Stats


def compute_time_span(df: pd.DataFrame, fcn: FileColumnNames):
    assert fcn.timestamp in df.columns

    return df[fcn.timestamp].iloc[-1] - df[fcn.timestamp].iloc[0]


def l3_pairs_count(df: pd.DataFrame, fcn: FileColumnNames):
    assert fcn.l3_communication_id in df.columns

    return df[fcn.l3_communication_id].nunique()


def l4_pairs_count(df: pd.DataFrame, fcn: FileColumnNames):
    assert fcn.l4_communication_id in df.columns

    return df[fcn.l4_communication_id].nunique()


# endregion


# region Plotting


def plot_pair_flow(df: pd.DataFrame, fcn: FileColumnNames, pair_id: int, axes: Axes):
    dff = df[df[fcn.l4_pair_id] == pair_id]
    dff = dsc.expand_values_to_columns(dff, fcn.l4_communication_id)
    print(dff)
    # TODO zde pokracovat

    time_series = pd.Series(dff[fcn.timestamp].index, index=dff[fcn.timestamp])
    ts = time_series.resample("30min").count()

    x = ts.index
    y = ts.values
    print(x)
    print(y)

    axes.plot(x, y, color="tab:orange")

    axes.set_xlabel("Time")
    axes.set_ylabel("Packet count")
    axes.set_title("Packet count in time")
    axes.grid(True)

    axes.xaxis.set_major_locator(AutoDateLocator())
    axes.xaxis.set_major_formatter(DateFormatter("%H:%M"))

    # plt.xlim([min(x), max(x)])
    # plt.ylim([0, max(y)])


# endregion
