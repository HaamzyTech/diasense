from app.core.time import to_iso8601
from app.repositories.pipeline_repository import PipelineRepository


class PipelineService:
    def __init__(self, pipeline_repo: PipelineRepository) -> None:
        self.pipeline_repo = pipeline_repo

    def list_runs(self, limit: int = 20) -> dict:
        items = self.pipeline_repo.list_runs(limit=limit)
        normalized_items: list[dict] = []
        for item in items:
            normalized_items.append(
                {
                    **item,
                    "id": str(item["id"]) if item.get("id") is not None else None,
                    "started_at": to_iso8601(item.get("started_at")),
                    "ended_at": to_iso8601(item.get("ended_at")),
                }
            )
        return {"items": normalized_items, "count": len(normalized_items)}

    def latest_status(self) -> str:
        return self.pipeline_repo.latest_status()

    def latest_run(self) -> dict | None:
        row = self.pipeline_repo.latest_run()
        if row is None:
            return None
        return {
            **row,
            "id": str(row["id"]) if row.get("id") is not None else None,
            "started_at": to_iso8601(row.get("started_at")),
            "ended_at": to_iso8601(row.get("ended_at")),
        }
