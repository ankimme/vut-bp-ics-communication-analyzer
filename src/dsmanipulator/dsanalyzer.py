from matplotlib.dates import DateFormatter, AutoDateLocator
from matplotlib.axes import Axes
import pandas as pd
import seaborn as sns

from . import dscreator as dsc
from .utils.dataobjects import Direction, FileColumnNames, Station

from bidict import bidict

# region Stats


def get_df_time_span(df: pd.DataFrame, fcn: FileColumnNames) -> pd.Timedelta:
    """Get timespan of whole dataframe. From start to end.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    fcn : FileColumnNames
        Real names of predefined columns.

    Returns
    -------
    pd.Timedelta
        Timespan of data in dataframe.
    """
    assert fcn.timestamp in df.columns

    return df[fcn.timestamp].iloc[-1] - df[fcn.timestamp].iloc[0]


# endregion


# region Dataframe Insights


def detect_master_staion(
    station_ids: bidict[int, Station], double_column_station: bool, port: int = 2404
) -> int | None:
    """Try to detect the master station by its port. Return the first found with corresponding port.

    Parameters
    ----------
    station_ids : bidict[int, Station]
        Key : ID of station.
        Value : Station.
    double_column_station : bool
        Whether station is described by two columns i.e. ip + port.

    Returns
    -------
    int | None
        ID of master station. None if not found.
    """
    pass

    for station_id, station in station_ids.items():
        if double_column_station:
            if station.port == port:
                return station_id
        else:
            if str(port) in station.ip:
                return station_id
    else:
        return None


# ids of stations that communicate with the master station
def get_connected_stations(pair_ids: bidict[int, frozenset], station_id: int) -> list[int]:
    """Get ids of stations that are communicating with given station.

    Parameters
    ----------
    pair_ids : bidict[int, frozenset]
        Key : ID of station.
        Value : Pair of station ids.
    station_id : int
        ID of station of interest.

    Returns
    -------
    list[int]
        Stations communicating with station of interest.
    """
    connected_ids = set()
    for pair in pair_ids.values():
        if station_id in pair:
            x, y = pair
            connected_ids.add(x)
            connected_ids.add(y)
    connected_ids.discard(station_id)

    return list(connected_ids)


# endregion


# region Plotting


def plot_pair_flow(
    df: pd.DataFrame,
    fcn: FileColumnNames,
    axes: Axes,
    pair_id: int,
    station_ids: bidict[int, Station],
    direction_ids: bidict[int, Direction],
) -> None:
    #     # TODO doc
    assert all(col in df.columns for col in [fcn.timestamp, fcn.pair_id, fcn.direction_id])

    # filter original dataframe and expand values
    tmpdf = df[df[fcn.pair_id] == pair_id]
    tmpdf = dsc.expand_values_to_columns(tmpdf, fcn.direction_id, drop_column=True)

    # names of expanded columns
    expanded_cols: list[str] = list(filter(lambda x: fcn.direction_id in x, tmpdf.columns))

    # filter only timestamp and expanded columns
    tmpdf = tmpdf[[fcn.timestamp] + expanded_cols]

    # rename expanded cols so that the legend shows relevant information
    renamed_cols: dict[str, str] = {}
    for col in expanded_cols:
        # TODO parse error
        direction_id = int(col.rsplit(":", 1)[1])
        src_station = station_ids[direction_ids[direction_id].src]
        dst_station = station_ids[direction_ids[direction_id].dst]
        renamed_cols[col] = f"{src_station} -> {dst_station}"

    tmpdf = tmpdf.rename(columns=renamed_cols)

    # convert index to datetimeindex for resampling
    tmpdf = dsc.convert_to_timeseries(tmpdf, fcn)
    tmpdf = tmpdf.resample("5min").sum()

    # create column with sum
    tmpdf.insert(0, "Sum", 0)
    tmpdf["Sum"] = tmpdf.sum(axis=1)

    # axes.set_xlabel("Time")
    # axes.set_ylabel("Packet count")
    # axes.set_title("Packet count in time")
    axes.grid(True)

    axes.xaxis.set_major_locator(AutoDateLocator())
    axes.xaxis.set_major_formatter(DateFormatter("%H:%M"))

    # plt.xlim([min(tmpdf.index), max(tmpdf.index)])
    # print(min(k))
    # print(max(k))
    # k = pd.DatetimeIndex(df[fcn.timestamp])
    # axes.set_xlim([min(k), max(k)])

    sns.lineplot(data=tmpdf, palette="tab10", linewidth=2.5, ax=axes)

    # axes.xaxis.set_major_locator(AutoDateLocator())
    # axes.xaxis.set_major_formatter(DateFormatter("%H:%M"))

    # plt.xlim([min(x), max(x)])
    # plt.ylim([0, max(y)])


def plot_slaves(
    df: pd.DataFrame,
    fcn: FileColumnNames,
    axes: Axes,
    station_ids: bidict[int, Station],
    direction_ids: bidict[int, Direction],
) -> None:
    #     # TODO doc

    tmpdf = dsc.expand_values_to_columns(df, fcn.pair_id, drop_column=True)

    # names of expanded columns
    expanded_cols: list[str] = list(filter(lambda x: fcn.pair_id in x, tmpdf.columns))

    # filter only timestamp and expanded columns
    tmpdf = tmpdf[[fcn.timestamp] + expanded_cols]

    tmpdf = dsc.convert_to_timeseries(tmpdf, fcn)
    tmpdf = tmpdf.resample("5min").sum()

    axes.xaxis.set_major_locator(AutoDateLocator())
    axes.xaxis.set_major_formatter(DateFormatter("%H:%M"))

    axes.legend([], [], frameon=False)

    sns.lineplot(data=tmpdf, palette="tab10", linewidth=2.5, ax=axes, legend=None)


# endregion
