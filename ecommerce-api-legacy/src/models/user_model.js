const crypto = require('crypto');
const { run, get, all } = require('../database/connection');

function hashPassword(plain) {
    const salt = crypto.randomBytes(16).toString('hex');
    const hash = crypto.scryptSync(plain, salt, 64).toString('hex');
    return `${salt}:${hash}`;
}

function verifyPassword(plain, stored) {
    const [salt, hash] = stored.split(':');
    const derived = crypto.scryptSync(plain, salt, 64);
    return crypto.timingSafeEqual(Buffer.from(hash, 'hex'), derived);
}

async function findByEmail(db, email) {
    return get(db, 'SELECT * FROM users WHERE email = ?', [email]);
}

async function findById(db, id) {
    return get(db, 'SELECT * FROM users WHERE id = ?', [id]);
}

async function create(db, { name, email, password }) {
    const hash = hashPassword(password || '123456');
    const result = await run(db, 'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [name, email, hash]);
    return { id: result.lastID, name, email };
}

async function remove(db, id) {
    const enrollments = await all(db, 'SELECT id FROM enrollments WHERE user_id = ?', [id]);
    for (const enrollment of enrollments) {
        await run(db, 'DELETE FROM payments WHERE enrollment_id = ?', [enrollment.id]);
    }
    await run(db, 'DELETE FROM enrollments WHERE user_id = ?', [id]);
    await run(db, 'DELETE FROM users WHERE id = ?', [id]);
}

module.exports = { hashPassword, verifyPassword, findByEmail, findById, create, remove };
