from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("paicer")
except PackageNotFoundError:
    __version__ = "dev"
