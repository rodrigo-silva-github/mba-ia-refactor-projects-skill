const userModel = require('../models/user_model');
const courseModel = require('../models/course_model');
const enrollmentModel = require('../models/enrollment_model');
const paymentModel = require('../models/payment_model');

async function seed(db) {
    const user = await userModel.create(db, { name: 'Leonan', email: 'leonan@fullcycle.com.br', password: '123' });
    const cleanArchitecture = await courseModel.create(db, { title: 'Clean Architecture', price: 997.0, active: 1 });
    await courseModel.create(db, { title: 'Docker', price: 497.0, active: 1 });

    const enrollment = await enrollmentModel.create(db, { userId: user.id, courseId: cleanArchitecture.id });
    await paymentModel.create(db, { enrollmentId: enrollment.id, amount: 997.0, status: paymentModel.STATUS.PAID });
}

module.exports = seed;
