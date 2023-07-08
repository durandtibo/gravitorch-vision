from __future__ import annotations

__all__ = ["DatasetCreator"]

from typing import TypeVar

from gravitorch.data.datasets import setup_dataset
from gravitorch.engines.base import BaseEngine
from gravitorch.utils.format import str_indent, str_mapping
from torch.utils.data import Dataset

from gtvision.creators.dataset.base import BaseDatasetCreator

T = TypeVar("T")


class DatasetCreator(BaseDatasetCreator[T]):
    r"""Implements a simple dataset creator.

    Args:
    ----
        dataset (``torch.utils.data.Dataset`` or dict): Specifies
            the dataset or its configuration.
        cache (bool, optional): If ``True``, the dataset is created
            only the first time, and then the same data is returned
            for each call to the ``create`` method.
            Default: ``False``

    Example usage:

    .. code-block:: pycon

        >>> from gtvision.creators.dataset import DatasetCreator
        >>> creator = DatasetCreator(
        ...     {
        ...         "_target_": "gravitorch.data.datasets.DummyMultiClassDataset",
        ...         "num_examples": 10,
        ...         "num_classes": 2,
        ...         "feature_size": 4,
        ...     }
        ... )
        >>> creator.create()  # doctest: +ELLIPSIS
        DummyMultiClassDataset(num_examples=10, num_classes=2, feature_size=4, noise_std=0.2, ...)
    """

    def __init__(self, dataset: Dataset[T] | dict, cache: bool = False) -> None:
        self._dataset = dataset
        self._cache = bool(cache)

    def __repr__(self) -> str:
        config = {"dataset": self._dataset, "cache": self._cache}
        return (
            f"{self.__class__.__qualname__}(\n"
            f"  {str_indent(str_mapping(config, sorted_keys=True))}\n)"
        )

    def create(self, engine: BaseEngine | None = None) -> Dataset[T]:
        dataset = setup_dataset(self._dataset)
        if self._cache:
            self._dataset = dataset
        return dataset
