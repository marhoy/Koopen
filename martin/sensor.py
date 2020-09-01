"""Implements sensor class."""
import logging
import re
from pathlib import Path
from typing import Tuple

import pandas as pd

logger = logging.getLogger(__name__)


def create_raw_data_file():
    """Read all CSV-files and write one Parquet file."""
    raw_data_files = Path("../Raw Data").glob("*.csv")
    data = pd.concat(
        (
            pd.read_csv(file, index_col=0, parse_dates=[0])
            for file in sorted(
                raw_data_files, key=lambda f: int(re.search(r"\d+", str(f)).group(0))
            )
        )
    )
    data.to_parquet("raw_data_all.parquet")


class BatterySavingSensor:
    """A sensor that measures with low frequency."""

    def __init__(
        self,
        inital_period="5 min",
        min_period="5 min",
        max_period="1 hour",
        period_increment="10 min",
        deadband=3,
    ):
        """Initialize class instance."""
        self.measurement_period = pd.Timedelta(inital_period)
        self.min_period = pd.Timedelta(min_period)
        self.max_period = pd.Timedelta(max_period)
        self.period_increment = pd.Timedelta(period_increment)
        self.deadband = deadband
        self.init_values()

    def init_values(self) -> None:
        """Reset internal values before a new simulation."""
        self.transmitted = pd.Series(dtype=float)
        self.measured = pd.Series(dtype=float)
        self.last_transmitted = -1000.0

    def measure(
        self, data: pd.Series, timestamp: pd.Timestamp
    ) -> Tuple[pd.Timestamp, float]:
        """Fake a measurement from the provided data."""
        timestamp = data.index.asof(timestamp)
        value = data.loc[timestamp]
        self.measured = self.measured.append(pd.Series(value, index=[timestamp]))
        return timestamp, value

    def transmit(self, timestamp: pd.Timestamp, value: float) -> None:
        """Fake a transmission."""
        self.transmitted = self.transmitted.append(pd.Series(value, index=[timestamp]))
        self.last_transmitted = value

    def longer_measurement_period(self) -> None:
        """Increase measurement period."""
        self.measurement_period = min(
            self.max_period, self.measurement_period + self.period_increment
        )
        # self.measurement_period = min(self.max_period, self.measurement_period * 2)

    def shorter_measurement_period(self) -> None:
        """Decrease measurement period."""
        self.measurement_period = self.min_period
        # self.measurement_period = max(self.min_period, self.measurement_period / 2)
        # self.measurement_period = max(
        #     self.min_period, self.measurement_period - self.period_increment
        # )

    def simulate(self, data: pd.Series) -> None:
        """Simulate sensor behaviour on provided data."""
        self.init_values()

        time = data.index[0]
        while time <= data.index[-1]:
            # Make a measurement
            timestamp, value = self.measure(data, time)

            # Compare measurement to last transmitted
            if abs(value - self.last_transmitted) > self.deadband:
                self.transmit(timestamp, value)
                self.shorter_measurement_period()
            else:
                self.longer_measurement_period()

            # Increment time
            time += self.measurement_period
