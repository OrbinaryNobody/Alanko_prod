from sqlalchemy.orm import Session
from core.access import AccessContext
from core.permissions import ROLE_PERMISSIONS
from repositories.user_repository import user_repository


class AccessService:
    def __init__(self, user_repository=None):
        self.user_repository = user_repository or user_repository

    def build_context(self, payload: dict, db: Session) -> AccessContext:
        if not payload or payload.get("user_id") is None:
            raise ValueError("Invalid authentication payload")

        user_id = payload["user_id"]
        email = payload.get("email")

        roles = self._resolve_roles(payload, db)
        permissions = self._resolve_permissions(roles)
        is_admin = "admin" in roles

        return AccessContext.from_parts(
            user_id=user_id,
            roles=roles,
            permissions=permissions,
            is_admin=is_admin,
            email=email,
        )

    def _resolve_roles(self, payload: dict, db: Session) -> set[str]:
        roles = set()
        token_role = payload.get("role")
        if token_role:
            roles.add(token_role)

        if payload.get("user_id") is None:
            return roles

        user = self.user_repository.get_by_id(db, payload["user_id"])
        if not user:
            return roles

        for user_role in user.roles:
            if user_role.role and user_role.role.name:
                roles.add(user_role.role.name)

        return roles

    def _resolve_permissions(self, roles: set[str]) -> set[str]:
        permissions = set()
        for role in roles:
            permissions.update(ROLE_PERMISSIONS.get(role, set()))
        return permissions


access_service = AccessService()
