"""Seed DesignFolio with repeatable development data.

Run from the backend directory:
    python seed.py

The script fills missing demo records until there are at least 8 users and
30 works. Set SEED_PASSWORD in the environment to choose the password used
by generated demo users.
"""
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from passlib.context import CryptContext
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import SessionLocal
from app.models import Category, Tag, User, Work, WorkImage, WorkTag

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SEED_PASSWORD = os.getenv("SEED_PASSWORD", "DesignFolio123!")

CATEGORIES = [
    ("UI/UX", "ui-ux", "Интерфейсы, пользовательский опыт и цифровые продукты."),
    ("3D", "3d", "Трёхмерная графика и визуализация."),
    ("Иллюстрация", "illustration", "Цифровые и авторские иллюстрации."),
]

TAGS = [
    ("Web", "web"),
    ("Mobile", "mobile"),
    ("Branding", "branding"),
    ("3D", "3d"),
    ("Illustration", "illustration"),
    ("Typography", "typography"),
]

DEMO_USERS = [
    ("alex", "alex@example.com", "designer"),
    ("maria", "maria@example.com", "designer"),
    ("nikita", "nikita@example.com", "designer"),
    ("sofia", "sofia@example.com", "designer"),
    ("daniel", "daniel@example.com", "designer"),
    ("kate", "kate@example.com", "designer"),
    ("viewer", "viewer@example.com", "viewer"),
    ("admin", "admin@example.com", "admin"),
]


def now():
    return datetime.now(timezone.utc)


def slugify(value: str) -> str:
    return "-".join(value.lower().replace("/", " ").split()).replace(" ", "-")


def unique_work_slug(db, base: str) -> str:
    slug = slugify(base)
    candidate = slug
    index = 2
    while db.scalar(select(Work).where(Work.slug == candidate)):
        candidate = f"{slug}-{index}"
        index += 1
    return candidate


def get_or_create_catalog(db):
    categories = {}
    for name, slug, description in CATEGORIES:
        item = db.scalar(select(Category).where(Category.slug == slug))
        if item is None:
            item = Category(name=name, slug=slug, description=description)
            db.add(item)
            db.flush()
        categories[slug] = item

    tags = {}
    for name, slug in TAGS:
        item = db.scalar(select(Tag).where(Tag.slug == slug))
        if item is None:
            item = Tag(name=name, slug=slug)
            db.add(item)
            db.flush()

    return categories, tags


def get_or_create_users(db):
    users = {}
    password_hash = pwd_context.hash(SEED_PASSWORD)

    for username, email, role in DEMO_USERS:
        user = db.scalar(select(User).where(User.username == username))
        if user is None:
            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                role=role,
                created_at=now(),
                updated_at=now(),
            )
            db.add(user)
            db.flush()
        users[username] = user

    return users


def seed_works(db, users, categories, tags):
    current_count = db.scalar(select(Work.id).order_by(Work.id.desc()).limit(1))
    current_count = db.scalar(select(Work).count()) if False else None
    target = 30

    designers = [users[name] for name, _, role in DEMO_USERS if role == "designer"]
    category_list = list(categories.values())
    tag_list = list(tags.values())

    existing_count = db.scalar(select(Work.id).limit(1))
    if existing_count is None:
        current_total = 0
    else:
        current_total = len(db.scalars(select(Work.id)).all())

    created = 0
    for index in range(current_total + 1, target + 1):
        author = designers[(index - 1) % len(designers)]
        category = category_list[(index - 1) % len(category_list)]
        title = f"DesignFolio Project {index:02d}"

        work = Work(
            author_id=author.id,
            category_id=category.id,
            title=title,
            slug=unique_work_slug(db, title),
            description=f"Демонстрационная работа DesignFolio №{index}. Проект для проверки каталога, фильтров и карточки работы.",
            cover_url=f"https://placehold.co/1200x800/png?text=Work+{index}",
            is_hidden=False,
            created_at=now(),
            updated_at=now(),
        )
        db.add(work)
        db.flush()

        db.add(WorkImage(
            work_id=work.id,
            image_url=f"https://placehold.co/1200x800/png?text=Work+{index}",
            sort_order=0,
            created_at=now(),
        ))

        first_tag = tag_list[(index - 1) % len(tag_list)]
        second_tag = tag_list[index % len(tag_list)]
        db.add(WorkTag(work_id=work.id, tag_id=first_tag.id))
        if second_tag.id != first_tag.id:
            db.add(WorkTag(work_id=work.id, tag_id=second_tag.id))
        created += 1

    return created


def main():
    db = SessionLocal()
    try:
        categories, tags = get_or_create_catalog(db)
        users = get_or_create_users(db)
        created = seed_works(db, users, categories, tags)
        db.commit()

        print(
            f"Seed complete: users={len(users)}, categories={len(categories)}, "
            f"tags={len(tags)}, works_created={created}"
        )
        print(f"Demo password: {SEED_PASSWORD}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
