from app.core.exceptions import NotFoundError
from app.repositories.model_version_repository import ModelVersionRepository


class ModelRegistryService:
    def __init__(self, model_repo: ModelVersionRepository) -> None:
        self.model_repo = model_repo

    def get_active_model(self) -> dict:
        model = self.model_repo.get_active()
        if not model:
            raise NotFoundError("No active model version found")
        return model
