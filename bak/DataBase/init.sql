--================================
-- Роли
--================================
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

--================================
-- Пользователи
--================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT,
    middle_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

--================================
-- Роли пользователей (many-to-many)
--================================
CREATE TABLE user_roles (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

--================================
-- Профили студентов
--================================
CREATE TABLE student_profiles (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    rating_points INTEGER DEFAULT 0,
    level TEXT DEFAULT 'beginner',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

--================================
-- Категории упражнений
--================================
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT
);

--================================
-- Задания (упражнения)
--================================
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    video_url TEXT, -- демонстрационное видео упражнения
    difficulty INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

--================================
-- Выполнение заданий студентами
-- (видео здесь = доказательство выполнения)
--================================
CREATE TABLE student_tasks (
    id SERIAL PRIMARY KEY,
    
    student_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,

    status TEXT DEFAULT 'not_started', 
    -- not_started | in_progress | done

    video_url TEXT,  -- видео выполнения ученика

    score INTEGER DEFAULT 0,
    comment TEXT,

    submitted_at TIMESTAMP WITH TIME ZONE,
    reviewed_at TIMESTAMP WITH TIME ZONE,

    UNIQUE(student_id, task_id)
);

--================================
-- Галерея (контент студии)
--================================
CREATE TABLE gallery (
    id SERIAL PRIMARY KEY,
    image_url TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

--================================
-- История рейтинга
--================================
CREATE TABLE ratings_history (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    points_change INTEGER NOT NULL,
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

--================================
-- Индексы (оптимизация поиска)
--================================
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);

CREATE INDEX idx_student_tasks_student_id ON student_tasks(student_id);
CREATE INDEX idx_student_tasks_task_id ON student_tasks(task_id);

CREATE INDEX idx_ratings_student_id ON ratings_history(student_id);

CREATE INDEX idx_tasks_category_id ON tasks(category_id);