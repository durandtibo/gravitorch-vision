from __future__ import annotations

__all__ = [
    "SequentialDataPipeCreator",
    "create_sequential_datapipe",
]

from collections.abc import Sequence

from gravitorch.engines.base import BaseEngine
from gravitorch.utils.format import str_indent, str_torch_sequence
from objectory import OBJECT_TARGET, factory
from torch.utils.data.graph import DataPipe

from gtvision.creators.datapipe.base import BaseDataPipeCreator


class SequentialDataPipeCreator(BaseDataPipeCreator):
    r"""Implements an ``DataPipe`` creator to create a sequence of
    ``DataPipe``s from their configuration.

    Args:
    ----
        config (dict or sequence of dict): Specifies the configuration
            of the ``DataPipe`` object to create. See description
            of the ``create_sequential_datapipe`` function to
            learn more about the expected values.

    Raises:
    ------
        ValueError if the ``DataPipe`` configuration sequence is
            empty.
    """

    def __init__(self, config: dict | Sequence[dict]) -> None:
        if not config:
            raise ValueError("It is not possible to create a DataPipe because config is empty")
        self._config = config

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__qualname__}(\n"
            f"  {str_indent(str_torch_sequence(self._config))},\n)"
        )

    def create(
        self, engine: BaseEngine | None = None, source_inputs: Sequence | None = None
    ) -> DataPipe:
        r"""Creates an ``DataPipe`` object.

        Args:
        ----
            engine (``BaseEngine`` or ``None``, optional): Specifies
                an engine. The engine is not used by this creator.
                Default: ``None``
            source_inputs (sequence or ``None``): Specifies the first
                positional arguments of the source ``DataPipe``.
                This argument can be used to create a new
                ``DataPipe`` object, that takes existing
                ``DataPipe`` objects as input. See examples below
                to see how to use it. If ``None``, ``source_inputs`` is
                set to an empty tuple. Default: ``None``

        Returns:
        -------
            ``DataPipe``: The created ``DataPipe`` object.

        Example usage:

        .. code-block:: pycon

            >>> from torch.utils.data.graph import DataPipe
            >>> from objectory import OBJECT_TARGET
            >>> from gtvision.creators.datapipe import SequentialDataPipeCreator
            # Create an DataPipe object using a single DataPipe object and no source input
            >>> creator = SequentialDataPipeCreator(
            ...     {
            ...         OBJECT_TARGET: "gravitorch.datapipes.iter.SourceWrapper",
            ...         "data": [1, 2, 3, 4],
            ...     }
            ... )
            >>> datapipe: DataPipe = creator.create()
            >>> tuple(datapipe)
            (1, 2, 3, 4)
            # Equivalent to
            >>> creator = SequentialDataPipeCreator(
            ...     [
            ...         {
            ...             OBJECT_TARGET: "gravitorch.datapipes.iter.SourceWrapper",
            ...             "data": [1, 2, 3, 4],
            ...         },
            ...     ]
            ... )
            >>> datapipe: DataPipe = creator.create()
            >>> tuple(datapipe)
            (1, 2, 3, 4)
            # It is possible to use the source_inputs to create the same DataPipe object.
            # The data is given by the source_inputs
            >>> creator = SequentialDataPipeCreator(
            ...     config={OBJECT_TARGET: "gravitorch.datapipes.iter.SourceWrapper"},
            ... )
            >>> datapipe: DataPipe = creator.create(source_inputs=([1, 2, 3, 4],))
            >>> tuple(datapipe)
            (1, 2, 3, 4)
            # Create an DataPipe object using two DataPipe objects and no source input
            >>> creator = SequentialDataPipeCreator(
            ...     [
            ...         {
            ...             OBJECT_TARGET: "gravitorch.datapipes.iter.SourceWrapper",
            ...             "data": [1, 2, 3, 4],
            ...         },
            ...         {
            ...             OBJECT_TARGET: "torch.utils.data.datapipes.iter.Batcher",
            ...             "batch_size": 2,
            ...         },
            ...     ]
            ... )
            >>> datapipe: DataPipe = creator.create()
            >>> tuple(datapipe)
            ([1, 2], [3, 4])
            # It is possible to use the source_inputs to create the same DataPipe object.
            # A source DataPipe object is specified by using source_inputs
            >>> creator = SequentialDataPipeCreator(
            ...     config=[
            ...         {
            ...             OBJECT_TARGET: "torch.utils.data.datapipes.iter.Batcher",
            ...             "batch_size": 2,
            ...         },
            ...     ],
            ... )
            >>> from gravitorch.datapipes.iter import SourceWrapper
            >>> datapipe: DataPipe = creator.create(source_inputs=[SourceWrapper(data=[1, 2, 3, 4])])
            >>> tuple(datapipe)
            ([1, 2], [3, 4])
            # It is possible to create a sequential ``DataPipe`` object that takes several
            # DataPipe objects as input.
            >>> creator = SequentialDataPipeCreator(
            ...     config=[
            ...         {OBJECT_TARGET: "torch.utils.data.datapipes.iter.Multiplexer"},
            ...         {
            ...             OBJECT_TARGET: "torch.utils.data.datapipes.iter.Batcher",
            ...             "batch_size": 2,
            ...         },
            ...     ],
            ... )
            >>> datapipe: DataPipe = creator.create(
            ...     source_inputs=[
            ...         SourceWrapper(data=[1, 2, 3, 4]),
            ...         SourceWrapper(data=[11, 12, 13, 14]),
            ...     ],
            ... )
            >>> tuple(datapipe)
            ([1, 11], [2, 12], [3, 13], [4, 14])
        """
        return create_sequential_datapipe(config=self._config, source_inputs=source_inputs)


def create_sequential_datapipe(
    config: dict | Sequence[dict],
    source_inputs: Sequence | None = None,
) -> DataPipe:
    r"""Creates a sequential ``DataPipe`` object.

    A sequential ``DataPipe`` object has a single source (which
    can takes multiple ``DataPipe`` objects) and a single sink.
    The structure should look like:

        SourceDatapipe -> DataPipe1 -> DataPipe2 -> SinkDataPipe

    The structure of the ``config`` input depends on the sequential
    ``DataPipe`` object that is created:

        - If ``config`` is a ``dict`` object, it creates a sequential
            ``DataPipe`` object with a single ``DataPipe``
            object. The dictionary should contain the parameters used
            to initialize the ``DataPipe`` object. It should
            follow the ``object_factory`` syntax. Using a dict allows
            to initialize a single ``DataPipe`` object. If you
            want to create a ``DataPipe`` object recursively, you
            need to give a sequence of dict.
        - If ``config`` is a sequence of ``dict`` objects, this
            function creates an ``DataPipe`` object with a
            sequential structure. The sequence of configurations
            follows the order of the ``DataPipe``s. The first
            config is used to create the first ``DataPipe``
            (a.k.a. source), and the last config is used to create the
            last ``DataPipe`` (a.k.a. sink). This function assumes
            all the DataPipes have a single source DataPipe as their
            first argument, excepts for the source ``DataPipe``.

    Note: it is possible to create sequential ``DataPipe`` objects
    without using this function.

    Args:
    ----
        config (dict or sequence of dict): Specifies the configuration
            of the ``DataPipe`` object to create. See description
            above to know when to use a dict or a sequence of dicts.
        source_inputs (sequence or ``None``): Specifies the first
            positional arguments of the source ``DataPipe``. This
            argument can be used to create a new ``DataPipe``
            object, that takes existing ``DataPipe`` objects as
            input. See examples below to see how to use it.
            If ``None``, ``source_inputs`` is set to an empty tuple.
            Default: ``None``

    Returns:
    -------
        ``DataPipe``: The last (a.k.a. sink) ``DataPipe`` of
            the sequence.

    Raises:
    ------
        RuntimeError if the configuration is empty (empty dict or
            sequence).

    Example usage:

    .. code-block:: pycon

        >>> from torch.utils.data.graph import DataPipe
        >>> from objectory import OBJECT_TARGET
        >>> from gtvision.creators.datapipe.sequential import create_sequential_datapipe
        # Create an DataPipe object using a single DataPipe object and no source input
        >>> datapipe: DataPipe = create_sequential_datapipe(
        ...     {
        ...         OBJECT_TARGET: "gravitorch.datapipes.iter.SourceWrapper",
        ...         "data": [1, 2, 3, 4],
        ...     }
        ... )
        >>> tuple(datapipe)
        (1, 2, 3, 4)
        # Equivalent to
        >>> datapipe: DataPipe = create_sequential_datapipe(
        ...     [
        ...         {
        ...             OBJECT_TARGET: "gravitorch.datapipes.iter.SourceWrapper",
        ...             "data": [1, 2, 3, 4],
        ...         },
        ...     ]
        ... )
        >>> tuple(datapipe)
        (1, 2, 3, 4)
        # It is possible to use the source_inputs to create the same DataPipe object.
        # The data is given by the source_inputs
        >>> datapipe: DataPipe = create_sequential_datapipe(
        ...     config={OBJECT_TARGET: "gravitorch.datapipes.iter.SourceWrapper"},
        ...     source_inputs=([1, 2, 3, 4],),
        ... )
        >>> tuple(datapipe)
        (1, 2, 3, 4)
        # Create an DataPipe object using two DataPipe objects and no source input
        >>> datapipe: DataPipe = create_sequential_datapipe(
        ...     [
        ...         {
        ...             OBJECT_TARGET: "gravitorch.datapipes.iter.SourceWrapper",
        ...             "data": [1, 2, 3, 4],
        ...         },
        ...         {OBJECT_TARGET: "torch.utils.data.datapipes.iter.Batcher", "batch_size": 2},
        ...     ]
        ... )
        >>> tuple(datapipe)
        ([1, 2], [3, 4])
        # It is possible to use the source_inputs to create the same DataPipe object.
        # A source DataPipe object is specified by using source_inputs
        >>> from gravitorch.datapipes.iter import SourceWrapper
        >>> datapipe: DataPipe = create_sequential_datapipe(
        ...     config=[
        ...         {OBJECT_TARGET: "torch.utils.data.datapipes.iter.Batcher", "batch_size": 2},
        ...     ],
        ...     source_inputs=[SourceWrapper(data=[1, 2, 3, 4])],
        ... )
        >>> tuple(datapipe)
        ([1, 2], [3, 4])
        # It is possible to create a sequential ``DataPipe`` object that takes several
        # DataPipe objects as input.
        >>> datapipe: DataPipe = create_sequential_datapipe(
        ...     config=[
        ...         {OBJECT_TARGET: "torch.utils.data.datapipes.iter.Multiplexer"},
        ...         {OBJECT_TARGET: "torch.utils.data.datapipes.iter.Batcher", "batch_size": 2},
        ...     ],
        ...     source_inputs=[
        ...         SourceWrapper(data=[1, 2, 3, 4]),
        ...         SourceWrapper(data=[11, 12, 13, 14]),
        ...     ],
        ... )
        >>> tuple(datapipe)
        ([1, 11], [2, 12], [3, 13], [4, 14])
    """
    if not config:
        raise RuntimeError("It is not possible to create a DataPipe because config is empty")
    source_inputs = source_inputs or ()
    if isinstance(config, dict):
        config = config.copy()  # Make a copy because the dict is modified below.
        target = config.pop(OBJECT_TARGET)
        return factory(target, *source_inputs, **config)
    datapipe = create_sequential_datapipe(config[0], source_inputs)
    for cfg in config[1:]:
        datapipe = create_sequential_datapipe(cfg, source_inputs=(datapipe,))
    return datapipe