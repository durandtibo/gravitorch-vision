from pathlib import Path
from unittest.mock import Mock

import torch
from gravitorch import constants as ct
from gravitorch.creators.dataloader import DataLoaderCreator
from gravitorch.utils.asset import AssetNotFoundError
from gravitorch.utils.io import save_pytorch
from pytest import TempPathFactory, fixture, raises
from torch.utils.data import DataLoader

from gtvision.datasources import MNISTDataSource


@fixture(scope="module")
def mnist_path(tmp_path_factory: TempPathFactory) -> Path:
    num_examples = 5
    mock_data = (
        torch.zeros(num_examples, 28, 28, dtype=torch.uint8),
        torch.zeros(num_examples, dtype=torch.long),
    )
    path = tmp_path_factory.mktemp("data")
    save_pytorch(mock_data, path.joinpath("MNIST/processed/training.pt"))
    save_pytorch(mock_data, path.joinpath("MNIST/processed/test.pt"))
    return path


#####################################
#     Tests for MNISTDataSource     #
#####################################


def test_mnist_data_source_str(mnist_path: Path) -> None:
    assert str(
        MNISTDataSource(path=mnist_path, data_loader_creators={ct.TRAIN: None, ct.EVAL: None})
    ).startswith("MNISTDataSource(")


def test_mnist_data_source_attach(mnist_path: Path) -> None:
    MNISTDataSource(path=mnist_path, data_loader_creators={ct.TRAIN: None, ct.EVAL: None}).attach(
        engine=Mock()
    )


def test_mnist_data_source_get_data_loader_train(mnist_path: Path) -> None:
    data_source = MNISTDataSource(
        path=mnist_path, data_loader_creators={ct.TRAIN: None, ct.EVAL: None}
    )
    assert isinstance(data_source.get_data_loader(ct.TRAIN), DataLoader)


def test_mnist_data_source_get_data_loader_eval(mnist_path: Path) -> None:
    data_source = MNISTDataSource(
        path=mnist_path, data_loader_creators={ct.TRAIN: None, ct.EVAL: None}
    )
    assert isinstance(data_source.get_data_loader(ct.EVAL), DataLoader)


def test_mnist_data_source_get_data_loader_batch_size_16(mnist_path: Path) -> None:
    data_source = MNISTDataSource(
        path=mnist_path,
        data_loader_creators={ct.TRAIN: DataLoaderCreator(batch_size=16), ct.EVAL: None},
    )
    loader = data_source.get_data_loader(ct.TRAIN)
    assert isinstance(loader, DataLoader)
    assert loader.batch_size == 16


def test_mnist_data_source_get_asset(mnist_path: Path) -> None:
    data_source = MNISTDataSource(
        path=mnist_path, data_loader_creators={ct.TRAIN: None, ct.EVAL: None}
    )
    with raises(AssetNotFoundError, match="The asset 'something' does not exist"):
        data_source.get_asset("something")


def test_mnist_data_source_has_asset(mnist_path: Path) -> None:
    data_source = MNISTDataSource(
        path=mnist_path, data_loader_creators={ct.TRAIN: None, ct.EVAL: None}
    )
    assert not data_source.has_asset("something")


def test_mnist_data_source_load_state_dict(mnist_path: Path) -> None:
    data_source = MNISTDataSource(
        path=mnist_path, data_loader_creators={ct.TRAIN: None, ct.EVAL: None}
    )
    data_source.load_state_dict({})


def test_mnist_data_source_state_dict(mnist_path: Path) -> None:
    data_source = MNISTDataSource(
        path=mnist_path, data_loader_creators={ct.TRAIN: None, ct.EVAL: None}
    )
    assert data_source.state_dict() == {}
