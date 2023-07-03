from __future__ import annotations

__all__ = ["DataLoaderDataFlowCreator"]

from typing import TypeVar

from gravitorch.data.dataloaders import is_dataloader_config
from gravitorch.engines.base import BaseEngine
from gravitorch.experimental.dataflow.dataloader import DataLoaderDataFlow
from torch.utils.data import DataLoader

from gtvision.creators.dataflow.base import BaseDataFlowCreator
from gtvision.creators.dataloader import (
    VanillaDataLoaderCreator,
    setup_data_loader_creator,
)
from gtvision.creators.dataloader.base import BaseDataLoaderCreator

T = TypeVar("T")


class DataLoaderDataFlowCreator(BaseDataFlowCreator):
    r"""Implements a simple ``DataLoaderDataFlow`` creator.

    Args:
    ----
        dataset (``torch.utils.data.DataLoader``): Specifies a
            data loader (or its configuration) or a data loader
            creator (or its configuration).
    """

    def __init__(self, dataloader: DataLoader | BaseDataLoaderCreator | dict) -> None:
        if isinstance(dataloader, DataLoader) or (
            isinstance(dataloader, dict) and is_dataloader_config(dataloader)
        ):
            dataloader = VanillaDataLoaderCreator(dataloader)
        self._dataloader = setup_data_loader_creator(dataloader)

    def __str__(self) -> str:
        return f"{self.__class__.__qualname__}()"

    def create(self, engine: BaseEngine | None = None) -> DataLoaderDataFlow[T]:
        return DataLoaderDataFlow(self._dataloader.create(engine))
