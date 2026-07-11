const express = require('express');
const asyncHandler = require('../middlewares/async_handler');
const requireAdmin = require('../middlewares/admin_auth');
const adminController = require('../controllers/admin_controller');

const router = express.Router();

router.get('/admin/financial-report', requireAdmin, asyncHandler(adminController.financialReport));

module.exports = router;
