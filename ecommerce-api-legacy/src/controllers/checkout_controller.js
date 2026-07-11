const userModel = require('../models/user_model');
const courseModel = require('../models/course_model');
const enrollmentModel = require('../models/enrollment_model');
const paymentModel = require('../models/payment_model');
const auditLogModel = require('../models/audit_log_model');
const logger = require('../config/logger');

const APPROVED_CARD_PREFIX = '4';

async function checkout(req, res) {
    const { usr, eml, pwd, c_id: courseId, card } = req.body;
    const db = req.app.locals.db;

    const course = await courseModel.findActiveById(db, courseId);
    if (!course) return res.status(404).send('Curso não encontrado');

    let user = await userModel.findByEmail(db, eml);
    if (!user) {
        user = await userModel.create(db, { name: usr, email: eml, password: pwd });
    }

    logger.info(`Processando pagamento do curso ${courseId} para o usuário ${user.id}`);
    const status = card.startsWith(APPROVED_CARD_PREFIX) ? paymentModel.STATUS.PAID : paymentModel.STATUS.DENIED;
    if (status === paymentModel.STATUS.DENIED) {
        return res.status(400).send('Pagamento recusado');
    }

    const enrollment = await enrollmentModel.create(db, { userId: user.id, courseId });
    await paymentModel.create(db, { enrollmentId: enrollment.id, amount: course.price, status });
    await auditLogModel.record(db, `Checkout curso ${courseId} por ${user.id}`);

    res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollment.id });
}

module.exports = { checkout };
