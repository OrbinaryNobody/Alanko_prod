from accounts.facade import accounts_facade
from schemas.auth import AdminAddUserSchema


class AdminUserService:
    def create_user_by_admin(self, db, data: AdminAddUserSchema):
        return accounts_facade.add_user_by_admin(db, data=data)


admin_user_service = AdminUserService()
