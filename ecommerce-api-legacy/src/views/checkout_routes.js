const express = require('express');
const asyncHandler = require('../middlewares/async_handler');
const checkoutController = require('../controllers/checkout_controller');

const router = express.Router();

router.post('/checkout', (req, res, next) => {
    const { usr, eml, c_id, card } = req.body;
    if (!usr || !eml || !c_id || !card) {
        return res.status(400).send('Bad Request');
    }
    return asyncHandler(checkoutController.checkout)(req, res, next);
});

module.exports = router;
