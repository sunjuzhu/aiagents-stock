from notification_service import notification_service
if notification_service.test_email_config():
    print("✅ 邮件配置正常")
else:
    print("❌ 邮件配置有问题")