# DesignFolio — ER-диаграмма и структура БД

Основные таблицы: users, works, categories, tags, work_images, comments, likes. Связующая таблица work_tags реализует many-to-many между works и tags.

~~~mermaid
erDiagram
    USERS ||--o{ WORKS : creates
    CATEGORIES ||--o{ WORKS : contains
    WORKS ||--o{ WORK_IMAGES : has
    USERS ||--o{ COMMENTS : writes
    WORKS ||--o{ COMMENTS : receives
    USERS ||--o{ LIKES : gives
    WORKS ||--o{ LIKES : receives
    WORKS ||--o{ WORK_TAGS : uses
    TAGS ||--o{ WORK_TAGS : assigned
    USERS { int id PK varchar username UK varchar email UK varchar password_hash varchar role varchar avatar_url text bio varchar contact_url boolean is_blocked timestamp created_at timestamp updated_at }
    CATEGORIES { int id PK varchar name UK varchar slug UK text description }
    WORKS { int id PK int user_id FK int category_id FK varchar title text description boolean is_hidden timestamp created_at timestamp updated_at }
    WORK_IMAGES { int id PK int work_id FK varchar file_url varchar alt_text int sort_order timestamp created_at }
    TAGS { int id PK varchar name UK varchar slug UK }
    WORK_TAGS { int work_id PK_FK int tag_id PK_FK }
    COMMENTS { int id PK int work_id FK int user_id FK text text boolean is_hidden timestamp created_at }
    LIKES { int user_id PK_FK int work_id PK_FK timestamp created_at }
~~~

Связи: users 1:N works; categories 1:N works; works 1:N work_images; users 1:N comments; works 1:N comments; users N:M works через likes; works N:M tags через work_tags. Составные ключи likes и work_tags запрещают дубликаты связей.