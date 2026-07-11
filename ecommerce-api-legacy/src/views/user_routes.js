const express = require('express');
const asyncHandler = require('../middlewares/async_handler');
const requireAdmin = require('../middlewares/admin_auth');
const userController = require('../controllers/user_controller');

const router = express.Router();

router.delete('/users/:id', requireAdmin, asyncHandler(userController.remove));

module.exports = router;
