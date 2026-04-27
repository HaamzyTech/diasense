from uuid import UUID

from app.core.auth_context import CurrentUser
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.core.time import to_iso8601
from app.repositories.auth_user_repository import AuthUserRepository
from app.services.auth_service import AuthService
from app.services.auth_service import VALID_ROLES


class UserService:
    def __init__(
        self,
        auth_user_repo: AuthUserRepository,
        auth_service: AuthService,
    ) -> None:
        self.auth_user_repo = auth_user_repo
        self.auth_service = auth_service

    def list_users(self, current_user: CurrentUser, limit: int = 200) -> dict:
        self._require_admin(current_user)
        items = [
            {
                "id": row["id"],
                "username": row["username"],
                "email": row.get("email"),
                "role": row["role"],
                "created_at": to_iso8601(row["created_at"]),
            }
            for row in self.auth_user_repo.list_users(limit=limit)
        ]
        return {"items": items, "count": len(items)}

    def update_user_role(self, current_user: CurrentUser, user_id: UUID, role: str) -> dict:
        self._require_admin(current_user)
        if role not in VALID_ROLES:
            raise ValidationError("Invalid role")

        updated = self.auth_user_repo.update_role(user_id=user_id, role=role)
        if updated is None:
            raise NotFoundError(f"User {user_id} not found")

        return {
            "id": updated["id"],
            "username": updated["username"],
            "email": updated.get("email"),
            "role": updated["role"],
            "created_at": to_iso8601(updated["created_at"]),
        }

    def delete_user(self, current_user: CurrentUser, user_id: UUID) -> dict:
        self._require_admin(current_user)
        target = self.auth_user_repo.get_by_id(user_id)
        if target is None:
            raise NotFoundError(f"User {user_id} not found")

        if current_user.auth_source == "database" and current_user.username == str(target["username"]):
            raise ValidationError("You can't delete your own account while signed in")

        deleted = self.auth_user_repo.delete_user(user_id=user_id)
        if deleted is None:
            raise NotFoundError(f"User {user_id} not found")

        return {
            "message": "User deleted successfully",
            "user": {
                "id": deleted["id"],
                "username": deleted["username"],
                "email": deleted.get("email"),
                "role": deleted["role"],
                "created_at": to_iso8601(deleted["created_at"]),
            },
        }

    def create_patient(
        self,
        current_user: CurrentUser,
        username: str | None,
        email: str | None,
        password: str,
    ) -> dict:
        self._require_clinical_access(current_user)
        signup_result = self.auth_service.signup(username=username, email=email, password=password)
        created_user = self.auth_user_repo.get_by_username(signup_result["user"]["username"])
        if created_user is None:
            raise NotFoundError("The patient account was created but could not be reloaded")

        return {
            "message": "Patient account created successfully",
            "patient": {
                "id": created_user["id"],
                "username": created_user["username"],
                "email": created_user.get("email"),
                "role": created_user["role"],
                "created_at": to_iso8601(created_user["created_at"]),
            },
        }

    def delete_patient(self, current_user: CurrentUser, user_id: UUID) -> dict:
        self._require_clinical_access(current_user)
        target = self.auth_user_repo.get_by_id(user_id)
        if target is None:
            raise NotFoundError(f"Patient {user_id} not found")

        if str(target["role"]) != "patient":
            raise ValidationError("Only patient accounts can be deleted from patient management")

        if current_user.auth_source == "database" and current_user.username == str(target["username"]):
            raise ValidationError("You can't delete your own account while signed in")

        deleted = self.auth_user_repo.delete_user(user_id=user_id)
        if deleted is None:
            raise NotFoundError(f"Patient {user_id} not found")

        return {
            "message": "Patient account deleted successfully",
            "patient": {
                "id": deleted["id"],
                "username": deleted["username"],
                "email": deleted.get("email"),
                "role": deleted["role"],
                "created_at": to_iso8601(deleted["created_at"]),
            },
        }

    def list_patients(self, current_user: CurrentUser, limit: int = 200) -> dict:
        self._require_clinical_access(current_user)
        items = []
        for row in self.auth_user_repo.list_patient_summaries(limit=limit):
            latest_risk_probability = row.get("latest_risk_probability")
            items.append(
                {
                    "id": row["id"],
                    "username": row["username"],
                    "email": row.get("email"),
                    "role": row["role"],
                    "created_at": to_iso8601(row["created_at"]),
                    "assessment_count": int(row.get("assessment_count", 0) or 0),
                    "last_assessed_at": (
                        to_iso8601(row["last_assessed_at"])
                        if row.get("last_assessed_at") is not None
                        else None
                    ),
                    "latest_risk_band": row.get("latest_risk_band"),
                    "latest_risk_probability": (
                        round(float(latest_risk_probability), 4)
                        if latest_risk_probability is not None
                        else None
                    ),
                }
            )
        return {"items": items, "count": len(items)}

    def _require_admin(self, current_user: CurrentUser) -> None:
        if current_user.role != "admin":
            raise AuthorizationError()

    def _require_clinical_access(self, current_user: CurrentUser) -> None:
        if current_user.role not in {"clinician", "admin"}:
            raise AuthorizationError()
