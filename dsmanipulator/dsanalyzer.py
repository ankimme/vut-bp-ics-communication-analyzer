import pandas as pd

from . import dscreator as dsc
from .utils.dataobjects import FileColumnNames


def compute_time_span(df: pd.DataFrame, fcn: FileColumnNames):

    assert fcn.timestamp in df.columns

    return df[fcn.timestamp].iloc[-1] - df[fcn.timestamp].iloc[0]
