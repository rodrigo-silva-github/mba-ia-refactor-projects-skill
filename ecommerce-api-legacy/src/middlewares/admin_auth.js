const { config } = require('../config');

function requireAdmin(req, res, next) {
    const providedKey = req.headers['x-admin-key'];
    if (!providedKey || providedKey !== config.adminApiKey) {
        return res.status(401).json({ error: 'Não autorizado' });
    }
    next();
}

module.exports = requireAdmin;
