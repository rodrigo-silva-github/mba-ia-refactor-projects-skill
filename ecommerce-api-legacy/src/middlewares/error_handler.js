const logger = require('../config/logger');

function errorHandler(err, req, res, next) {
    logger.error('Erro não tratado', err);
    res.status(500).json({ error: 'Erro interno no servidor' });
}

module.exports = errorHandler;
