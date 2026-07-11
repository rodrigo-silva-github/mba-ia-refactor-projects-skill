const express = require('express');
const { config } = require('./config');
const logger = require('./config/logger');
const { createConnection, createSchema } = require('./database/connection');
const seed = require('./database/seed');
const errorHandler = require('./middlewares/error_handler');
const checkoutRoutes = require('./views/checkout_routes');
const adminRoutes = require('./views/admin_routes');
const userRoutes = require('./views/user_routes');

async function bootstrap() {
    const app = express();
    app.use(express.json());

    const db = createConnection();
    await createSchema(db);
    await seed(db);
    app.locals.db = db;

    app.use('/api', checkoutRoutes);
    app.use('/api', adminRoutes);
    app.use('/api', userRoutes);

    app.use(errorHandler);

    app.listen(config.port, () => {
        logger.info(`Frankenstein LMS rodando na porta ${config.port}...`);
    });
}

bootstrap();
