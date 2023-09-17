from __future__ import annotations

__all__ = ["DistributedDataLoaderCreator"]

from typing import TypeVar

from gravitorch.data.dataloaders import create_dataloader
from gravitorch.data.datasets import is_dataset_config
from gravitorch.distributed import comm as dist
from gravitorch.engines.base import BaseEngine
from gravitorch.utils.format import str_indent, str_mapping
from gravitorch.utils.seed import get_torch_generator
from torch.utils.data import DataLoader, Dataset, DistributedSampler

from gtvision.creators.dataloader.base import BaseDataLoaderCreator
from gtvision.creators.dataset.base import BaseDatasetCreator, setup_dataset_creator
from gtvision.creators.dataset.vanilla import DatasetCreator

T = TypeVar("T")


class DistributedDataLoaderCreator(BaseDataLoaderCreator[T]):
    r"""Defines a simple distributed PyTorch dataloader creator.

    This dataloader creator uses the ``gravitorch.distributed`` package
    to distribute the example per process. Note that this dataloader
    creator uses the default samplers. If you need a different sampler,
    you will need to implement your own dataloader creator.

    Args:
    ----
        dataset (``torch.utils.data.Dataset``): Specifies a
            dataset (or its configuration) or a dataset creator
            (or its configuration).
        shuffle (bool, optional): Specifies of the examples are
            shuffled or not. You should set to ``True`` to have the
            data reshuffled at every epoch. Default: ``False``
        drop_last (bool, optional): set to ``True`` to drop the last
            incomplete batch, if the dataset size is not divisible by
            the batch size. If ``False`` and the size of dataset is
            not divisible by the batch size, then the last batch will
            be smaller. Default: ``False``
        seed (int, optional): Specifies the random seed used to
            shuffle the samples if ``shuffle=True``. Default: ``0``
        **kwargs: See ``torch.utils.data.DataLoader`` documentation.

    Example usage:

    .. code-block:: pycon

        >>> from gtvision.creators.dataloader import DistributedDataLoaderCreator
        >>> creator = DistributedDataLoaderCreator(
        ...     {
        ...         "_target_": "gravitorch.data.datasets.DummyMultiClassDataset",
        ...         "num_examples": 10,
        ...         "num_classes": 2,
        ...         "feature_size": 4,
        ...     }
        ... )
        >>> creator.create()
        <torch.utils.data.dataloader.DataLoader object at 0x...>
    """

    def __init__(
        self,
        dataset: Dataset | BaseDatasetCreator | dict,
        shuffle: bool = True,
        drop_last: bool = False,
        seed: int = 0,
        **kwargs,
    ) -> None:
        if isinstance(dataset, Dataset) or (
            isinstance(dataset, dict) and is_dataset_config(dataset)
        ):
            dataset = DatasetCreator(dataset)
        self._dataset = setup_dataset_creator(dataset)
        self._shuffle = bool(shuffle)
        self._drop_last = bool(drop_last)
        self._seed = int(seed)
        self._kwargs = kwargs

    def __repr__(self) -> str:
        config = {
            "dataset": self._dataset,
            "shuffle": self._shuffle,
            "drop_last": self._drop_last,
            "seed": self._seed,
        } | self._kwargs
        return (
            f"{self.__class__.__qualname__}(\n"
            f"  {str_indent(str_mapping(config, sorted_keys=True))}\n)"
        )

    def create(self, engine: BaseEngine | None = None) -> DataLoader[T]:
        dataset = self._dataset.create(engine)
        sampler = DistributedSampler(
            dataset,
            shuffle=self._shuffle,
            drop_last=self._drop_last,
            seed=self._seed,
            rank=dist.get_rank(),
            num_replicas=dist.get_world_size(),
        )
        epoch = 0
        if engine is not None:
            epoch = engine.epoch
            # In distributed mode, calling the set_epoch() method at the beginning
            # of each epoch before creating the DataLoader iterator is necessary to
            # make shuffling work properly across multiple epochs.
            # Otherwise, the same ordering will always be used.
            sampler.set_epoch(epoch)

        # Sampler option is mutually exclusive with shuffle or drop last.
        return create_dataloader(
            dataset,
            sampler=sampler,
            generator=get_torch_generator(self._seed + epoch),
            **self._kwargs,
        )
