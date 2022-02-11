import importlib.resources

resources = importlib.resources.files(__name__).joinpath('data')
