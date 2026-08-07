from sqlalchemy.orm import Session

from shared.access.access_context import AccessContext


class AccessService:
    def __init__(self, user_repository=None):
        self.user_repository = user_repository or None

    def build_context(self, payload: dict, db: Session) -> AccessContext:
        if not payload or payload.get("user_id") is None:
            raise ValueError("Invalid authentication payload")

        user_id = payload["user_id"]
        email = payload.get("email")
        roles = self._resolve_roles(payload)
        permissions = self._resolve_permissions(payload)
        is_admin = any(str(role).lower() == "admin" for role in roles)

        return AccessContext.from_parts(
            user_id=user_id,
            roles=roles,
            permissions=permissions,
            is_admin=is_admin,
            email=email,
        )

    def _resolve_roles(self, payload: dict) -> set[str]:
        roles: set[str] = set()
        for role_key in ("role", "roles", "role_names"):
            value = payload.get(role_key)
            if isinstance(value, str):
                roles.add(value)
            elif isinstance(value, (list, tuple, set)):
                roles.update(str(item) for item in value)
        return {str(role).strip() for role in roles if str(role).strip()}

    def _resolve_permissions(self, payload: dict) -> set[str]:
        permissions: set[str] = set()
        for permission_key in ("permissions", "scopes", "permission"):
            value = payload.get(permission_key)
            if isinstance(value, str):
                permissions.add(value)
            elif isinstance(value, (list, tuple, set)):
                permissions.update(str(permission) for permission in value)
        return permissions


access_service = AccessService()
