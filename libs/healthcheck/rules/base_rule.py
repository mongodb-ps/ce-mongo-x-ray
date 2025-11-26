"""Base class for health check rules."""

from abc import ABC, abstractmethod


class BaseRule(ABC):
    def __init__(self, thresholds: dict = None):
        self._thresholds = thresholds

    @abstractmethod
    def apply(self, data: object, **kwargs) -> tuple:
        raise NotImplementedError("Subclasses must implement the apply method")
