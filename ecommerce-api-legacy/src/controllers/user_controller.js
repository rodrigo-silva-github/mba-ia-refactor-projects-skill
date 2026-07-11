const userModel = require('../models/user_model');

async function remove(req, res) {
    const db = req.app.locals.db;
    await userModel.remove(db, req.params.id);
    res.send('Usuário e registros relacionados (matrículas e pagamentos) removidos com sucesso.');
}

module.exports = { remove };
