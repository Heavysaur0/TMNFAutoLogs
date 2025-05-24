import pickle


def save(data: dict, file_path: str) -> None:
    with open(file_path, "wb") as file:
        pickle.dump(data, file)


def load(file_path: str) -> dict:
    with open(file_path, "rb") as file:
        data = pickle.load(file)
    return data