import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, AutoDateLocator
from matplotlib.axes import Axes
import pandas as pd
import seaborn as sns

from . import dscreator as dsc
from .utils.dataobjects import FileColumnNames

from bidict import bidict
from dsmanipulator.utils.dataobjects import CommunicationPair

# region Stats


def compute_time_span(df: pd.DataFrame, fcn: FileColumnNames):
    assert fcn.timestamp in df.columns

    return df[fcn.timestamp].iloc[-1] - df[fcn.timestamp].iloc[0]


def pairs_count(df: pd.DataFrame, fcn: FileColumnNames):
    # TODO doc
    assert fcn.communication_id in df.columns

    return df[fcn.communication_id].nunique()


# endregion


# region Plotting


def plot_pair_flow(df: pd.DataFrame, fcn: FileColumnNames,  axes: Axes, pair_id: int, comm_pairs_l4: bidict[int, CommunicationPair]):
    assert all(col in df.columns for col in [fcn.timestamp, fcn.pair_id, fcn.communication_id])

    # filter original dataframe and expand values
    tmpdf = df[df[fcn.pair_id] == pair_id]
    tmpdf = dsc.expand_values_to_columns(tmpdf, fcn.communication_id, drop_column=True)

    # names of expanded columns
    expanded_cols: list[str] = list(filter(lambda x: fcn.communication_id in x, tmpdf.columns))

    # filter only timestamp and expanded columns
    tmpdf = tmpdf[expanded_cols + [fcn.timestamp]]

    # rename expanded cols so that the legend shows relevant information
    renamed_cols: dict[str, str] = {}
    for col in expanded_cols:
        comm_id = col.rsplit(':', 1)[1]
        # TODO error
        comm_pair = comm_pairs_l4[int(comm_id)]
        # line = tmpdf[tmpdf[fcn.l4_communication_id] == communication_id].head(1)
        if fcn.double_column_station:
            renamed_cols[col] = f"{comm_pair.src_ip}:{comm_pair.src_port} -> {comm_pair.dst_ip}:{comm_pair.dst_port}"
        else:
            # TODO test
            renamed_cols[col] = f"{comm_pair.src_ip} -> {comm_pair.dst_ip}"
    tmpdf = tmpdf.rename(columns=renamed_cols)

    # convert index to datetimeindex for resampling
    tmpdf = dsc.convert_to_timeseries(tmpdf, fcn)
    tmpdf = tmpdf.resample('30min').sum()

    # create column with sum
    tmpdf.insert(0, 'Sum', 0)
    tmpdf['Sum'] = tmpdf.sum(axis=1)

    axes.set_xlabel('Time')
    axes.set_ylabel('Packet count')
    axes.set_title('Packet count in time')
    axes.grid(True)

    axes.xaxis.set_major_locator(AutoDateLocator())
    axes.xaxis.set_major_formatter(DateFormatter('%H:%M'))

    # plt.xlim([min(tmpdf.index), max(tmpdf.index)])
    axes.set_xlim([min(tmpdf.index), max(tmpdf.index)])

    sns.lineplot(data=tmpdf, palette="tab10", linewidth=2.5, ax=axes)

    # axes.xaxis.set_major_locator(AutoDateLocator())
    # axes.xaxis.set_major_formatter(DateFormatter("%H:%M"))

    # plt.xlim([min(x), max(x)])
    # plt.ylim([0, max(y)])


# endregion
