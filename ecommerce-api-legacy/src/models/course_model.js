const { run, get, all } = require('../database/connection');

async function findActiveById(db, id) {
    return get(db, 'SELECT * FROM courses WHERE id = ? AND active = 1', [id]);
}

async function findAll(db) {
    return all(db, 'SELECT * FROM courses');
}

async function create(db, { title, price, active = 1 }) {
    const result = await run(db, 'INSERT INTO courses (title, price, active) VALUES (?, ?, ?)', [title, price, active]);
    return { id: result.lastID, title, price, active };
}

module.exports = { findActiveById, findAll, create };
