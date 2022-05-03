from re import A
from matplotlib.dates import DateFormatter, AutoDateLocator
from matplotlib.axes import Axes

import numpy as np
import pandas as pd
import seaborn as sns

from dsmanipulator import dscreator as dsc
from dsmanipulator.utils import Direction, FileColumnNames, Station, DirectionEnum


import random

from bidict import bidict

# region Dataframe Insights


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


def get_attribute_stats(
    df: pd.DataFrame, fcn: FileColumnNames, attribute_name: str, resample_rate: pd.Timedelta
) -> pd.DataFrame:
    tmpdf = df.loc[:, [fcn.timestamp, attribute_name]]

    tmpdf = dsc.convert_to_timeseries(tmpdf, fcn)
    tmpdf = dsc.expand_values_to_columns(tmpdf, attribute_name)
    tmpdf = tmpdf.resample(resample_rate).sum()
    tmpdf = tmpdf.rename(columns={og: og.lstrip(f"{attribute_name}:") for og in tmpdf.columns})

    data = []
    for attribute_value in tmpdf.columns:
        mean = tmpdf[attribute_value].mean()
        std = tmpdf[attribute_value].std()

        row = []
        row.append(attribute_value)
        row.append(mean)
        row.append(std)
        row.append(tmpdf[attribute_value].var())
        row.append(tmpdf[attribute_value].quantile(q=0.25))
        row.append(tmpdf[attribute_value].median())
        row.append(tmpdf[attribute_value].quantile(q=0.75))
        row.append(tmpdf[attribute_value].quantile(q=0.75) - tmpdf[attribute_value].quantile(q=0.25))
        row.append(mean - 3 * std)
        row.append(mean + 3 * std)
        row.append((mean + 3 * std) - (mean - 3 * std))
        row.append(len(tmpdf[attribute_value].loc[lambda x: ~x.between(mean - 3 * std, mean + 3 * std)]))

        data.append(row)

    return pd.DataFrame(
        data,
        columns=[
            "Attribute value",
            "Mean",
            "Standard deviation",
            "Variance",
            "Quantile 25%",
            "Median",
            "Quantile 75%",
            "IQR",
            "Minus 3 sigma",
            "Plus 3 sigma",
            "3 sigma interval size",
            "Values out of 3 sigma",
        ],
    )


def get_iat_stats_whole_df(df: pd.DataFrame, fcn: FileColumnNames):
    if len(df.index) == 0 or fcn.rel_time not in df.columns:
        return 0, 0, 0, 0

    # convert relative time to numpy array
    times = df[fcn.rel_time].values

    # create shifted array (first emlement is doubled and the rest is shifted right)
    shifted = np.concatenate((times[0:1], times[:-1]))

    # compute inter arrival time
    iats = times - shifted

    # drop first value because it is always zero
    iats = iats[1:]

    # np.savetxt("iats_whole_df.txt", iats)

    # mean, median, min, max
    if len(iats) > 0:
        return iats.mean(), np.median(iats), iats.min(), iats.max()
    else:
        return 0, 0, 0, 0


def get_iat_stats_filtered(
    df: pd.DataFrame,
    fcn: FileColumnNames,
    master_station_id: int,
    slave_station_ids: list[int],
    pair_ids: bidict[int, frozenset],
) -> tuple[int, int, int, int]:

    if len(df.index) == 0 or fcn.rel_time not in df.columns:
        return 0, 0, 0, 0

    all_iats = np.empty(0)

    for slave_id in slave_station_ids:
        pair_id = pair_ids.inv[frozenset({master_station_id, slave_id})]

        tmpdf = df[df[fcn.pair_id] == pair_id]

        # skip empty communications
        if len(tmpdf.index) == 0:
            continue

        # convert relative time to numpy array
        times = df[fcn.rel_time].values

        # create shifted array (first emlement is doubled and the rest is shifted right)
        shifted = np.concatenate((times[0:1], times[:-1]))

        # compute inter arrival time
        new_iats = times - shifted

        # drop first value because it is always zero
        new_iats = new_iats[1:]

        all_iats = np.concatenate((all_iats, new_iats))

    # np.savetxt("iats_filtered.txt", all_iats)

    if len(all_iats) > 0:
        # mean, median, min, max
        return all_iats.mean(), np.median(all_iats), all_iats.min(), all_iats.max()
    else:
        return 0, 0, 0, 0


def get_packet_count_by_direction(
    df: pd.DataFrame,
    fcn: FileColumnNames,
    master_station_id: int,
    slave_station_ids: list[int],
    direction_ids: bidict[int, Direction],
    direction: DirectionEnum,
) -> int:

    direction_ids = get_direction_ids_by_filter(master_station_id, slave_station_ids, direction, direction_ids)

    return len(df[df[fcn.direction_id].isin(direction_ids)])


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
    int
        ID of master station. If the detection fails return a random value.
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
        return random.choice(list(station_ids.keys()))


def get_connected_stations(pair_ids: bidict[int, frozenset], master_station_id: int) -> list[int]:
    """Get ids of stations that are communicating with master.

    Parameters
    ----------
    pair_ids : bidict[int, frozenset]
        Key : ID of pair.
        Value : Pair of station ids.
    master_station_id : int
        ID of master station.

    Returns
    -------
    list[int]
        Ids of stations communicating with master.
    """
    connected_ids = set()
    for pair in pair_ids.values():
        if master_station_id in pair:
            x, y = pair
            connected_ids.add(x)
            connected_ids.add(y)
    connected_ids.discard(master_station_id)

    return list(connected_ids)


def get_connected_pairs(
    master_station_id: int, slave_station_ids: list[int], pair_ids: bidict[int, frozenset]
) -> list[int]:
    """Get ids of communication pairs where the given master station and slave stations are involved.

    Parameters
    ----------
    master_station_id : int
        ID of master station.
    slave_station_ids : list[int]
        IDs of slave stations.
    pair_ids : bidict[int, frozenset]
        Key : ID of pair.
        Value : Pair of station ids.

    Returns
    -------
    list[int]
        IDs of pairs where master communicates with a slave from given list of slaves.
    """

    # all combinations of master station with slaves
    # as frozenset which are used for filtering
    pair_combinations: list[frozenset] = []
    for slave_station_id in slave_station_ids:
        pair_combinations.append(frozenset({master_station_id, slave_station_id}))

    # filter pair_ids so that only pairs containing the master station are present
    filtered_pair_ids: list[int] = [
        pair_id for pair_id, pair_set in pair_ids.items() if any(x for x in pair_combinations if x == pair_set)
    ]

    return filtered_pair_ids


def get_direction_ids_by_filter(
    master_station_id: int,
    slave_station_ids: list[int],
    direction: DirectionEnum,
    direction_ids: bidict[int, Direction],
) -> list[int]:
    """Get ids of directions where the given master station and slave stations are involved and are communicating in specified direcion.

    Parameters
    ----------
    master_station_id : int
        ID of master station.
    slave_station_ids : list[int]
        IDs of slave stations.
    direction : DirectionEnum
        Direction used for filtering.
    direction_ids : bidict[int, Direction]
        Key : ID of direction.
        Value : Pair of station ids. Source and destination.
        Direction does matter.

    Returns
    -------
    list[int]
        IDs of directions with specified filters applied.
    """

    # ids of directions where src=master and dst=slave
    m2s_ids: list[int] = [
        direction_id
        for direction_id, (src, dst) in direction_ids.items()
        if src == master_station_id and dst in slave_station_ids
    ]

    s2m_ids: list[int] = [
        direction_id
        for direction_id, (src, dst) in direction_ids.items()
        if dst == master_station_id and src in slave_station_ids
    ]

    match direction:
        case DirectionEnum.BOTH:
            return m2s_ids + s2m_ids
        case DirectionEnum.M2S:
            return m2s_ids
        case DirectionEnum.S2M:
            return s2m_ids
        case _:
            return []


# endregion


# region Plotting


def plot_pair_flow(
    df: pd.DataFrame,
    fcn: FileColumnNames,
    axes: Axes,
    pair_id: int,
    station_ids: bidict[int, Station],
    direction_ids: bidict[int, Direction],
    resample_rate: pd.Timedelta,
) -> None:
    # TODO doc
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
    tmpdf = tmpdf.resample(resample_rate).sum()

    # create column with sum
    tmpdf.insert(0, "Sum", 0)
    tmpdf["Sum"] = tmpdf.sum(axis=1)

    axes.set_xlabel("Time")
    axes.set_ylabel("Packet count")
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
    resample_rate: pd.Timedelta,
    master_station_id: int,
    station_ids: bidict[int, Station],
    pair_ids: bidict[int, frozenset],
) -> None:
    #     # TODO doc

    tmpdf = dsc.expand_values_to_columns(df, fcn.pair_id, drop_column=True)

    # names of expanded columns
    expanded_cols: list[str] = list(filter(lambda x: fcn.pair_id in x, tmpdf.columns))

    # filter only timestamp and expanded columns
    tmpdf = tmpdf[[fcn.timestamp] + expanded_cols]

    # rename columns to create legend
    new_col_names = {}
    for old_col_name in expanded_cols:
        x, y = pair_ids[int(old_col_name.rsplit(":", 1)[1])]
        slave_station_id = x if master_station_id == y else y
        new_col_names[old_col_name] = str(station_ids[slave_station_id])

    tmpdf.rename(columns=new_col_names, inplace=True)

    tmpdf = dsc.convert_to_timeseries(tmpdf, fcn)
    tmpdf = tmpdf.resample(resample_rate).sum()

    axes.xaxis.set_major_locator(AutoDateLocator())
    axes.xaxis.set_major_formatter(DateFormatter("%H:%M"))

    axes.legend([], [], loc="center right", frameon=False)

    sns.lineplot(data=tmpdf, palette="tab10", linewidth=2.5, ax=axes)


def plot_attribute_values(
    df: pd.DataFrame,
    fcn: FileColumnNames,
    attribute_name: str,
    resample_rate: pd.Timedelta,
    axes: Axes,
):

    tmpdf = df.loc[:, [fcn.timestamp, attribute_name]]

    tmpdf = dsc.convert_to_timeseries(tmpdf, fcn)
    tmpdf = dsc.expand_values_to_columns(tmpdf, attribute_name)
    tmpdf = tmpdf.resample(resample_rate).sum()
    tmpdf = tmpdf.rename(columns={og: og.lstrip(f"{attribute_name}:") for og in tmpdf.columns})

    left_xlim = min(tmpdf.index)
    right_xlim = max(tmpdf.index)
    axes.set_xlim([left_xlim, right_xlim])

    axes.xaxis.set_major_locator(AutoDateLocator())
    axes.xaxis.set_major_formatter(DateFormatter("%H:%M"))

    axes.legend([], [], loc="center right", frameon=False)

    sns.lineplot(data=tmpdf, palette="tab10", linewidth=2.5, ax=axes)


# endregion
