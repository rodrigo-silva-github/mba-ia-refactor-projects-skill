const { run } = require('../database/connection');

async function create(db, { userId, courseId }) {
    const result = await run(db, 'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [userId, courseId]);
    return { id: result.lastID, userId, courseId };
}

module.exports = { create };
