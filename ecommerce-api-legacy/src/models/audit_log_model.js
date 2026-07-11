const { run } = require('../database/connection');

async function record(db, action) {
    return run(db, "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [action]);
}

module.exports = { record };
