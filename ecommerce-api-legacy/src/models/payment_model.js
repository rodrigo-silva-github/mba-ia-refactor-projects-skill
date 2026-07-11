const { run } = require('../database/connection');

const STATUS = { PAID: 'PAID', DENIED: 'DENIED' };

async function create(db, { enrollmentId, amount, status }) {
    const result = await run(db, 'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)', [enrollmentId, amount, status]);
    return { id: result.lastID, enrollmentId, amount, status };
}

module.exports = { STATUS, create };
