const config = {
    port: parseInt(process.env.PORT || '3000', 10),
    dbUser: process.env.DB_USER || 'dev_user',
    dbPass: process.env.DB_PASS || 'dev_pass_change_me',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || 'pk_test_dev_change_me',
    smtpUser: process.env.SMTP_USER || 'dev@example.com',
    adminApiKey: process.env.ADMIN_API_KEY || 'dev-admin-key-change-me',
};

module.exports = { config };
