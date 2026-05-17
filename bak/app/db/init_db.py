from db.database import engine
from models import Base
from sqlalchemy import text
from core.security import hash_password

def init_db():
    print("=== INITIALIZING DATABASE ===")
    try:
        Base.metadata.create_all(bind=engine)
        print("=== DATABASE TABLES CREATED ===")
    except Exception as e:
        print(f"ERROR CREATING TABLES: {e}")
        return
    
    with engine.connect() as conn:

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
