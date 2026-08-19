from db.database import engine
from models.base import Base
from models.all_models import *  # noqa: F401,F403
from sqlalchemy import text
from core.security import hash_password

def init_db():
    print("=== INITIALIZING DATABASE ===")
    try:
        Base.metadata.create_all(bind=engine)
        print("=== DATABASE TABLES CREATED ===")
    except Exception as e:
        print(f"WARNING: create_all encountered a schema issue, continuing with idempotent init: {e}")
    
    with engine.connect() as conn:
        # Consultation schema is bootstrapped through Base.metadata.create_all.
        # Keep this index idempotent for databases created before the model update.
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_consultation_invitations_slot_student_status
                ON consultation_invitations (slot_id, student_id, status)
            """))
            conn.commit()
        except Exception as e:
            print(f"Failed to ensure consultation invitation index: {e}")
            conn.rollback()

        for column_name, column_definition in (
            ("price", "INTEGER NOT NULL DEFAULT 0"),
            ("currency", "VARCHAR(8) NOT NULL DEFAULT 'RUB'"),
        ):
            result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'consultation_slots' AND column_name = :column_name
            """), {"column_name": column_name})
            if not result.fetchone():
                try:
                    conn.execute(text(f"ALTER TABLE consultation_slots ADD COLUMN {column_name} {column_definition}"))
                    conn.commit()
                except Exception as e:
                    print(f"Failed to add consultation_slots.{column_name}: {e}")
                    conn.rollback()

        for column_name, column_definition in (
            ("payment_status", "VARCHAR(16) NOT NULL DEFAULT 'UNPAID'"),
            ("paid_at", "TIMESTAMP WITH TIME ZONE"),
        ):
            result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'consultation_participants' AND column_name = :column_name
            """), {"column_name": column_name})
            if not result.fetchone():
                try:
                    conn.execute(text(f"ALTER TABLE consultation_participants ADD COLUMN {column_name} {column_definition}"))
                    conn.commit()
                except Exception as e:
                    print(f"Failed to add consultation_participants.{column_name}: {e}")
                    conn.rollback()

        # Проверяем и добавляем уникальное ограничение для PENDING-платежей
        inspector_query = text("""
            SELECT constraint_name FROM information_schema.table_constraints
            WHERE table_name = 'payments' AND constraint_type = 'UNIQUE'
            AND constraint_name = 'uq_payments_user_offer_status'
        """)
        result = conn.execute(inspector_query)
        if not result.fetchone():
            try:
                conn.execute(text("""
                    ALTER TABLE payments
                    ADD CONSTRAINT uq_payments_user_offer_status UNIQUE (user_id, special_offer_id, status)
                """))
                conn.commit()
                print("Added unique constraint uq_payments_user_offer_status to payments")
            except Exception as e:
                print(f"Failed to add unique constraint uq_payments_user_offer_status: {e}")
                conn.rollback()

        # Проверяем и добавляем lifecycle-поля для special_offers
        inspector_query = text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'special_offers' AND column_name = 'status'
        """)
        result = conn.execute(inspector_query)
        if not result.fetchone():
            try:
                conn.execute(text("""
                    ALTER TABLE special_offers 
                    ADD COLUMN status TEXT NOT NULL DEFAULT 'DRAFT'
                """))
                conn.commit()
                print("Added status column to special_offers")
            except Exception as e:
                print(f"Failed to add status column to special_offers: {e}")
                conn.rollback()

        inspector_query = text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'special_offers' AND column_name = 'registration_opens_at'
        """)
        result = conn.execute(inspector_query)
        if not result.fetchone():
            try:
                conn.execute(text("""
                    ALTER TABLE special_offers 
                    ADD COLUMN registration_opens_at TIMESTAMP WITH TIME ZONE
                """))
                conn.commit()
                print("Added registration_opens_at column to special_offers")
            except Exception as e:
                print(f"Failed to add registration_opens_at column to special_offers: {e}")
                conn.rollback()

        inspector_query = text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'special_offers' AND column_name = 'registration_closes_at'
        """)
        result = conn.execute(inspector_query)
        if not result.fetchone():
            try:
                conn.execute(text("""
                    ALTER TABLE special_offers 
                    ADD COLUMN registration_closes_at TIMESTAMP WITH TIME ZONE
                """))
                conn.commit()
                print("Added registration_closes_at column to special_offers")
            except Exception as e:
                print(f"Failed to add registration_closes_at column to special_offers: {e}")
                conn.rollback()

        inspector_query = text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'special_offers' AND column_name = 'updated_at'
        """)
        result = conn.execute(inspector_query)
        if not result.fetchone():
            try:
                conn.execute(text("""
                    ALTER TABLE special_offers 
                    ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
                """))
                conn.commit()
                print("Added updated_at column to special_offers")
            except Exception as e:
                print(f"Failed to add updated_at column to special_offers: {e}")
                conn.rollback()

        inspector_query = text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'special_offers' AND column_name = 'is_active'
        """)
        result = conn.execute(inspector_query)
        if result.fetchone():
            try:
                conn.execute(text("""
                    UPDATE special_offers
                    SET status = CASE
                        WHEN status IS NULL OR status = '' THEN 'REGISTRATION_OPEN'
                        ELSE status
                    END
                    WHERE status IS NULL OR status = ''
                """))
                conn.execute(text("""
                    UPDATE special_offers
                    SET status = 'REGISTRATION_OPEN'
                    WHERE is_active = 'active'
                """))
                conn.execute(text("""
                    ALTER TABLE special_offers
                    DROP COLUMN is_active
                """))
                conn.commit()
                print("Migrated special_offers from is_active to lifecycle status")
            except Exception as e:
                print(f"Failed to migrate special_offers lifecycle columns: {e}")
                conn.rollback()

        # Проверяем и добавляем недостающие колонки в achievements
        inspector_query = text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'achievements' AND column_name = 'place'
        """)
        result = conn.execute(inspector_query)
        if not result.fetchone():
            # Колонка не существует, добавляем её
            try:
                conn.execute(text("""
                    ALTER TABLE achievements 
                    ADD COLUMN place TEXT
                """))
                conn.commit()
                print("Added place column to achievements")
            except Exception as e:
                print(f"Failed to add place column: {e}")
                conn.rollback()

        # Проверяем и добавляем is_collective
        inspector_query = text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'achievements' AND column_name = 'is_collective'
        """)
        result = conn.execute(inspector_query)
        if not result.fetchone():
            # Колонка не существует, добавляем её
            try:
                conn.execute(text("""
                    ALTER TABLE achievements 
                    ADD COLUMN is_collective BOOLEAN DEFAULT FALSE
                """))
                conn.commit()
                print("Added is_collective column to achievements")
            except Exception as e:
                print(f"Failed to add is_collective column: {e}")
                conn.rollback()
        inspector_query = text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'achievements' AND column_name = 'certificate_url'
        """)
        result = conn.execute(inspector_query)
        if not result.fetchone():
            try:
                conn.execute(text("""
                    ALTER TABLE achievements 
                    ADD COLUMN certificate_url TEXT
                """))
                conn.commit()
                print("Added certificate_url column to achievements")
            except Exception as e:
                print(f"Failed to add certificate_url column to achievements: {e}")
                conn.rollback()

        inspector_query = text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'achievements' AND column_name = 'video_url'
        """)
        result = conn.execute(inspector_query)
        if not result.fetchone():
            try:
                conn.execute(text("""
                    ALTER TABLE achievements 
                    ADD COLUMN video_url TEXT
                """))
                conn.commit()
                print("Added video_url column to achievements")
            except Exception as e:
                print(f"Failed to add video_url column to achievements: {e}")
                conn.rollback()

        inspector_query = text("""
            SELECT column_name FROM information_schema.columns             WHERE table_name = 'student_profiles' AND column_name = 'image_url'
        """)
        result = conn.execute(inspector_query)
        if not result.fetchone():
            # Колонка не существует, добавляем её
            try:
                conn.execute(text("""
                    ALTER TABLE student_profiles 
                    ADD COLUMN image_url TEXT NOT NULL DEFAULT 'default.jpg'
                """))
                conn.commit()
                print("Added image_url column to student_profiles")
            except Exception as e:
                print(f"Failed to add image_url column: {e}")
                conn.rollback()

        inspector_query = text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'student_profiles' AND column_name = 'birth_year'
        """)
        result = conn.execute(inspector_query)
        if not result.fetchone():
            try:
                conn.execute(text("""
                    ALTER TABLE student_profiles
                    ADD COLUMN birth_year INTEGER
                """))
                conn.commit()
                print("Added birth_year column to student_profiles")
            except Exception as e:
                print(f"Failed to add birth_year column to student_profiles: {e}")
                conn.rollback()

        inspector_query = text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'student_profiles' AND column_name = 'last_rank'
        """)
        result = conn.execute(inspector_query)
        if not result.fetchone():
            try:
                conn.execute(text("""
                    ALTER TABLE student_profiles 
                    ADD COLUMN last_rank INTEGER
                """))
                conn.commit()
                print("Added last_rank column to student_profiles")
            except Exception as e:
                print(f"Failed to add last_rank column to student_profiles: {e}")
                conn.rollback()

        inspector_query = text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'plain_password'
        """)
        result = conn.execute(inspector_query)
        if not result.fetchone():
            try:
                conn.execute(text("""
                    ALTER TABLE users
                    ADD COLUMN plain_password TEXT
                """))
                conn.commit()
                print("Added plain_password column to users")
            except Exception as e:
                print(f"Failed to add plain_password column to users: {e}")
                conn.rollback()

        # Проверяем и добавляем max_score в задания
        inspector_query = text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'tasks' AND column_name = 'max_score'
        """)
        result = conn.execute(inspector_query)
        if not result.fetchone():
            try:
                conn.execute(text("""
                    ALTER TABLE tasks 
                    ADD COLUMN max_score INTEGER DEFAULT 100
                """))
                conn.commit()
                print("Added max_score column to tasks")
            except Exception as e:
                print(f"Failed to add max_score column to tasks: {e}")
                conn.rollback()
        
        # Проверяем, есть ли роли
        result = conn.execute(text("SELECT COUNT(*) FROM roles"))

        count = result.fetchone()[0]
        if count == 0:
            # Вставляем роли
            conn.execute(text("""
                INSERT INTO roles (id, name) VALUES 
                (1, 'student'), 
                (2, 'admin'), 
                (3, 'teacher')
            """))
            conn.commit()
            print("Roles inserted into database")
        else:
            print("Roles already exist")
        
        # Проверяем, есть ли админ
        result = conn.execute(text("SELECT COUNT(*) FROM users WHERE email = 'admin@example.com'"))
        count = result.fetchone()[0]
        if count == 0:
            # Создаём админа
            hashed_password = hash_password("admin123")
            conn.execute(text(f"""
                INSERT INTO users (email, first_name, last_name, middle_name, password_hash) VALUES 
                ('admin@example.com', 'Admin', 'Adminov', 'Adminovich', '{hashed_password}')
            """))
            # Получаем id админа
            result = conn.execute(text("SELECT id FROM users WHERE email = 'admin@example.com'"))
            admin_id = result.fetchone()[0]
            # Присваиваем роль админа
            conn.execute(text(f"""
                INSERT INTO user_roles (user_id, role_id) VALUES 
                ({admin_id}, 2)
            """))
            conn.commit()
            print("Admin user created")
        else:
            print("Admin user already exists")
