from __future__ import annotations

__all__ = ["DictBatcherIterDataPipeCreator"]

from collections.abc import Sequence
from typing import TypeVar

from gravitorch.data.datacreators import BaseDataCreator, setup_datacreator
from gravitorch.datapipes.iter import DictBatcher
from gravitorch.engines.base import BaseEngine
from gravitorch.utils.format import str_indent, str_mapping
from torch import Tensor
from torch.utils.data import IterDataPipe, MapDataPipe

from gtvision.creators.datapipe.base import BaseDataPipeCreator

T = TypeVar("T")


class DictBatcherIterDataPipeCreator(BaseDataPipeCreator[T]):
    r"""Create a ``DictBatcher`` where the data is generated by a
    ``BaseDataCreator`` object.

    Args:
    ----
        data (``BaseDataCreator`` or ``dict``): Specifies the data
            creator or its configuration.
        **kwargs: See documentation of ``DictBatcher``

    Example usage:

    .. code-block:: pycon

        >>> import torch
        >>> from gravitorch.data.datacreators import DataCreator
        >>> from gtvision.creators.datapipe import DictBatcherIterDataPipeCreator
        >>> creator = DictBatcherIterDataPipeCreator(
        ...     DataCreator({"key": torch.ones(6, 3)}), batch_size=4
        ... )
        >>> datapipe = creator.create()
        >>> datapipe
        DictBatcherIterDataPipe(
        (batch_size): 4
          (shuffle): False
          (random_seed): 11918852809641073385
          (datapipe_or_data): <class 'dict'> (length=1)
              (key): <class 'torch.Tensor'> | shape=torch.Size([6, 3]) | dtype=torch.float32 | device=cpu
        )
    """

    def __init__(self, data: BaseDataCreator[dict[str, Tensor]] | dict, **kwargs) -> None:
        self._data = setup_datacreator(data)
        self._kwargs = kwargs

    def __repr__(self) -> str:
        config = {"data": self._data} | self._kwargs
        return (
            f"{self.__class__.__qualname__}(\n"
            f"  {str_indent(str_mapping(config, sorted_keys=True))}\n)"
        )

    def create(
        self, engine: BaseEngine | None = None, source_inputs: Sequence | None = None
    ) -> IterDataPipe[T] | MapDataPipe[T]:
        return DictBatcher(self._data.create(engine), **self._kwargs)
