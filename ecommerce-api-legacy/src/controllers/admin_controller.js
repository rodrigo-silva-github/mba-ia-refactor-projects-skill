const reportModel = require('../models/report_model');

async function financialReport(req, res) {
    const db = req.app.locals.db;
    const report = await reportModel.financialReport(db);
    res.json(report);
}

module.exports = { financialReport };
