import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(API + path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || "Ошибка запроса");
  }
  return response.status === 204 ? null : response.json();
}

function App() {
  const [works, setWorks] = useState([]);
  const [categories, setCategories] = useState([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [sort, setSort] = useState("newest");
  const [page, setPage] = useState(1);
  const [meta, setMeta] = useState({ pages: 0, total: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    request("/api/categories").then(setCategories).catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    const params = new URLSearchParams({ page, limit: 12, sort });
    if (search.trim()) params.set("search", search.trim());
    if (category) params.set("category_id", category);
    request("/api/works?" + params)
      .then((data) => {
        if (!cancelled) {
          setWorks(data.items);
          setMeta({ pages: data.pages, total: data.total });
        }
      })
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));
    return () => { cancelled = true; };
  }, [page, search, category, sort]);

  const resetFilters = () => {
    setSearch("");
    setCategory("");
    setSort("newest");
    setPage(1);
  };

  return (
    <div className="app">
      <header className="header">
        <div><strong>DesignFolio</strong><span>портфолио дизайнеров</span></div>
        <a href="#catalog">Каталог</a>
      </header>
      <main id="catalog">
        <section className="hero">
          <p className="eyebrow">DESIGNFOLIO</p>
          <h1>Работы студентов в одном каталоге.</h1>
          <p>UI/UX, 3D и иллюстрации. Поиск, фильтрация и сортировка работают через API и базу данных.</p>
        </section>
        <section className="toolbar">
          <input value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} placeholder="Поиск по работам..." />
          <select value={category} onChange={(e) => { setCategory(e.target.value); setPage(1); }}>
            <option value="">Все направления</option>
            {categories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select>
          <select value={sort} onChange={(e) => { setSort(e.target.value); setPage(1); }}>
            <option value="newest">Сначала новые</option>
            <option value="oldest">Сначала старые</option>
          </select>
          <button onClick={resetFilters}>Сбросить</button>
        </section>
        {loading && <div className="state">Загрузка каталога...</div>}
        {!loading && error && <div className="state error">{error}</div>}
        {!loading && !error && works.length === 0 && <div className="state">Работы не найдены.</div>}
        {!loading && !error && works.length > 0 && <>
          <div className="result-count">Найдено: {meta.total}</div>
          <section className="grid">
            {works.map((work) => <article className="card" key={work.id}>
              <img src={work.cover_url || "https://placehold.co/800x500/png?text=DesignFolio"} alt="" />
              <div className="card-body"><h2>{work.title}</h2><p>{work.description}</p><small>Работа #{work.id}</small></div>
            </article>)}
          </section>
          {meta.pages > 1 && <nav className="pagination">
            <button disabled={page <= 1} onClick={() => setPage(page - 1)}>Назад</button>
            <span>{page} / {meta.pages}</span>
            <button disabled={page >= meta.pages} onClick={() => setPage(page + 1)}>Вперёд</button>
          </nav>}
        </>}
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
