const { all } = require('../database/connection');

async function financialReport(db) {
    const rows = await all(db, `
        SELECT c.id AS course_id, c.title AS course_title,
               e.id AS enrollment_id, u.name AS student_name,
               p.amount AS paid_amount, p.status AS payment_status
        FROM courses c
        LEFT JOIN enrollments e ON e.course_id = c.id
        LEFT JOIN users u ON u.id = e.user_id
        LEFT JOIN payments p ON p.enrollment_id = e.id
        ORDER BY c.id
    `);

    const coursesById = new Map();
    for (const row of rows) {
        if (!coursesById.has(row.course_id)) {
            coursesById.set(row.course_id, { course: row.course_title, revenue: 0, students: [] });
        }

        if (row.enrollment_id === null || row.enrollment_id === undefined) continue;

        const courseData = coursesById.get(row.course_id);
        const paid = row.paid_amount || 0;
        if (row.payment_status === 'PAID') {
            courseData.revenue += paid;
        }
        courseData.students.push({ student: row.student_name || 'Unknown', paid });
    }

    return Array.from(coursesById.values());
}

module.exports = { financialReport };
