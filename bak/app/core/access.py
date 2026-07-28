from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, FrozenSet, Any


@dataclass(frozen=True)
class AccessContext:
    user_id: int
    roles: FrozenSet[str]
    permissions: FrozenSet[str]
    is_admin: bool = False
    email: str | None = None

    @classmethod
    def from_parts(
        cls,
        user_id: int,
        roles: Iterable[str],
        permissions: Iterable[str],
        is_admin: bool = False,
        email: str | None = None,
    ) -> "AccessContext":
        return cls(
            user_id=user_id,
            roles=frozenset(roles),
            permissions=frozenset(permissions),
            is_admin=is_admin,
            email=email,
        )

    def has_role(self, role: str) -> bool:
        return role in self.roles

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def __getitem__(self, key: str) -> Any:
        if key == "user_id":
            return self.user_id
        if key == "roles":
            return set(self.roles)
        if key == "permissions":
            return set(self.permissions)
        if key == "is_admin":
            return self.is_admin
        if key == "email":
            return self.email
        if key == "role":
            return next(iter(self.roles), None)
        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self.__getitem__(key)
        except KeyError:
            return default
