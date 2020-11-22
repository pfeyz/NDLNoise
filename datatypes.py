from datetime import datetime, timedelta
from typing import List
import dataclasses

from domain import GrammarId


@dataclasses.dataclass
class ExperimentParameters:
    languages: List[GrammarId]
    noise_levels: List[float]
    learningrate: float
    conservative_learningrate: float
    num_sentences: int
    num_echildren: int
    num_procs: int


@dataclasses.dataclass
class TrialParameters:
    """ The parameters for a single echild simulation """
    language: GrammarId
    noise: float
    rate: float
    conservativerate: float
    numberofsentences: int

    def as_dict(self):
        return dataclasses.asdict(self)


@dataclasses.dataclass
class NDResult:
    trial_params: TrialParameters
    timestamp: datetime
    duration: timedelta
    language: int
    grammar: dict

    @classmethod
    def csv_headers(cls):
        param_fields = [
            field.name for field in dataclasses.fields(TrialParameters)
        ]

        return [
            *param_fields, "SP", "HIP", "HCP", "OPT", "NS", "NT", "WHM", "PI",
            "TM", "VtoI", "ItoC", "AH", "QInv", "timestamp", "duration"
        ]

    def as_csv_row(self):
        row = dataclasses.asdict(self)
        trial_params = row.pop('trial_params')
        grammar = row.pop('grammar')
        row.update(trial_params)
        row.update(grammar)
        return row
