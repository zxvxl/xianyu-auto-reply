-- ============================================================
-- 闲鱼管理系统 · 完整表结构
-- 修改表结构请直接编辑本文件
--
-- 格式约定：每条 SQL 语句以分号结尾，语句之间用空行分隔。
-- bootstrap.py 按 ";\n\n" 分割执行，请勿在语句内部留空行。
-- ============================================================

-- [1] xy_users
CREATE TABLE IF NOT EXISTS xy_users (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
                external_id VARCHAR(64) COMMENT '外部ID',
                username VARCHAR(64) NOT NULL UNIQUE COMMENT '用户名',
                email VARCHAR(255) NOT NULL UNIQUE COMMENT '邮箱',
                phone VARCHAR(32) COMMENT '手机号',
                password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
                status ENUM('ACTIVE', 'INACTIVE', 'SUSPENDED', 'DELETED') DEFAULT 'ACTIVE' COMMENT '用户状态',
                role ENUM('ADMIN', 'OPERATOR', 'MEMBER') DEFAULT 'MEMBER' COMMENT '用户角色',
                account_limit INT DEFAULT NULL COMMENT '可添加账号数量',
                last_login_at DATETIME COMMENT '最后登录时间',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                login_fail_count INT DEFAULT 0 COMMENT '登录失败次数',
                login_locked_until DATETIME COMMENT '登录锁定截止时间',
                dock_code VARCHAR(32) DEFAULT NULL UNIQUE COMMENT '对接码，用于分销商识别',
                INDEX idx_external_id (external_id),
                INDEX idx_username (username),
                INDEX idx_email (email),
                INDEX idx_user_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- [2] xy_user_settings
CREATE TABLE IF NOT EXISTS xy_user_settings (
                id INT PRIMARY KEY AUTO_INCREMENT COMMENT '设置ID',
                user_id INT NOT NULL COMMENT '用户ID',
                `key` VARCHAR(120) NOT NULL COMMENT '设置键',
                value TEXT NOT NULL COMMENT '设置值',
                description TEXT COMMENT '设置描述',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_user_id (user_id),
                UNIQUE KEY uk_user_key (user_id, `key`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户设置表';

-- [3] xy_system_settings
CREATE TABLE IF NOT EXISTS xy_system_settings (
                `key` VARCHAR(120) PRIMARY KEY COMMENT '设置键',
                value TEXT NOT NULL COMMENT '设置值',
                description TEXT COMMENT '设置描述',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统设置表';

-- [4] xy_accounts
CREATE TABLE IF NOT EXISTS xy_accounts (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '账号ID',
                owner_id BIGINT NOT NULL COMMENT '所属用户ID',
                account_id VARCHAR(80) NOT NULL COMMENT '账号标识',
                display_name VARCHAR(120) COMMENT '显示名称',
                unb VARCHAR(64) COMMENT 'UNB标识',
                cookie TEXT NOT NULL COMMENT 'Cookie信息',
                login_method VARCHAR(20) NOT NULL COMMENT '登录方式',
                status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '账号状态',
                username VARCHAR(120) COMMENT '登录用户名',
                login_password TEXT COMMENT '登录密码',
                remark VARCHAR(255) COMMENT '备注',
                pause_duration INT DEFAULT 10 COMMENT '暂停时长(分钟)',
                auto_confirm TINYINT(1) DEFAULT 0 COMMENT '自动确认发货',
                show_browser TINYINT(1) DEFAULT 0 COMMENT '显示浏览器',
                metadata JSON COMMENT '元数据',
                last_login_at DATETIME COMMENT '最后登录时间',
                last_refresh_at DATETIME COMMENT '最后刷新时间',
                proxy_type VARCHAR(20) DEFAULT 'none' COMMENT '代理类型',
                proxy_host VARCHAR(255) COMMENT '代理主机',
                proxy_port INT COMMENT '代理端口',
                proxy_user VARCHAR(120) COMMENT '代理用户名',
                proxy_pass VARCHAR(255) COMMENT '代理密码',
                message_expire_time INT DEFAULT 3600 COMMENT '相同消息等待时间(秒)',
                disable_reason VARCHAR(255) COMMENT '禁用原因',
                scheduled_redelivery TINYINT(1) NOT NULL DEFAULT 0 COMMENT '定时补发货开关',
                scheduled_rate TINYINT(1) NOT NULL DEFAULT 0 COMMENT '定时补评价开关',
                auto_polish TINYINT(1) NOT NULL DEFAULT 0 COMMENT '商品自动擦亮开关',
                confirm_before_send TINYINT(1) NOT NULL DEFAULT 0 COMMENT '发货成功再发卡券开关',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                auto_red_flower TINYINT(1) NOT NULL DEFAULT 0 COMMENT '自动求小红花开关',
                delivery_disabled TINYINT(1) NOT NULL DEFAULT 0 COMMENT '禁止发货开关',
                delivery_disabled_reason VARCHAR(500) DEFAULT NULL COMMENT '禁止发货原因',
                auto_close_order TINYINT(1) NOT NULL DEFAULT 0 COMMENT '主动关闭订单开关',
                delivery_only_card_after_close TINYINT(1) NOT NULL DEFAULT 0 COMMENT '关闭订单后继续发货（只发卡券）',
                delivery_disabled_excluded_items JSON DEFAULT NULL COMMENT '禁止发货排除商品列表（item_id 数组，命中后按正常流程发货）',
                INDEX idx_owner_id (owner_id),
                INDEX idx_account_id (account_id),
                INDEX idx_unb (unb),
                INDEX idx_account_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='闲鱼账号表';

-- [5] xy_keyword_rules
CREATE TABLE IF NOT EXISTS xy_keyword_rules (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '规则ID',
                owner_id BIGINT NOT NULL COMMENT '所属用户ID',
                account_id BIGINT COMMENT '关联账号ID',
                keyword VARCHAR(120) NOT NULL COMMENT '关键词',
                reply_content TEXT COMMENT '回复内容',
                reply_type VARCHAR(16) COMMENT '回复类型(text/image)',
                image_url VARCHAR(512) COMMENT '图片URL',
                item_id VARCHAR(64) COMMENT '商品ID',
                priority INT DEFAULT 100 COMMENT '优先级',
                is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_owner_id (owner_id),
                INDEX idx_account_id (account_id),
                INDEX idx_keyword (keyword),
                INDEX idx_kw_account_item (account_id, item_id),
                INDEX idx_kw_account_active (account_id, is_active)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='关键词规则表';

-- [6] xy_catalog_items
CREATE TABLE IF NOT EXISTS xy_catalog_items (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '商品ID',
                owner_id BIGINT NOT NULL COMMENT '所属用户ID',
                account_id BIGINT NOT NULL COMMENT '关联账号ID',
                item_id VARCHAR(64) NOT NULL COMMENT '商品标识',
                title VARCHAR(255) COMMENT '商品标题',
                price VARCHAR(32) COMMENT '商品价格',
                ai_prompt TEXT COMMENT '商品AI提示词',
                is_polished TINYINT(1) DEFAULT 0 COMMENT '是否擦亮',
                metadata JSON COMMENT '商品元数据',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_owner_id (owner_id),
                INDEX idx_account_id (account_id),
                INDEX idx_item_id (item_id),
                INDEX idx_cat_account_item (account_id, item_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='商品目录表';

-- [7] xy_orders
CREATE TABLE IF NOT EXISTS xy_orders (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '订单ID',
                owner_id BIGINT NOT NULL COMMENT '所属用户ID',
                order_no VARCHAR(64) NOT NULL COMMENT '订单号',
                status VARCHAR(32) NOT NULL COMMENT '订单状态',
                buyer_nick VARCHAR(120) COMMENT '买家昵称',
                buyer_id VARCHAR(64) COMMENT '买家ID',
                chat_id VARCHAR(64) COMMENT '聊天会话ID',
                item_id VARCHAR(64) COMMENT '商品ID',
                spec_name VARCHAR(120) COMMENT '规格名称',
                spec_value VARCHAR(120) COMMENT '规格值',
                quantity INT DEFAULT 1 COMMENT '数量',
                amount DECIMAL(12,2) COMMENT '金额',
                currency VARCHAR(8) DEFAULT 'CNY' COMMENT '货币',
                account_id VARCHAR(64) COMMENT '账号标识',
                account_name VARCHAR(120) COMMENT '账号名称',
                is_bargain TINYINT(1) DEFAULT 0 COMMENT '是否小刀',
                receiver_name VARCHAR(120) COMMENT '收货人姓名',
                receiver_phone VARCHAR(32) COMMENT '收货人手机号',
                receiver_address VARCHAR(512) COMMENT '收货地址',
                delivery_fail_reason VARCHAR(2000) COMMENT '发货失败原因',
                item_snapshot JSON COMMENT '商品快照',
                metadata JSON COMMENT '元数据',
                source VARCHAR(32) COMMENT '数据来源：fetch_xianyu-获取闲鱼订单按钮',
                placed_at DATETIME COMMENT '下单时间',
                synced_at DATETIME COMMENT '同步时间',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                buyer_fish_nick VARCHAR(120) COMMENT '买家闲鱼昵称（明文）',
                is_rated TINYINT(1) DEFAULT 0 COMMENT '是否已评价',
                delivery_method VARCHAR(32) COMMENT '发货方式',
                delivery_content VARCHAR(2000) COMMENT '发货内容',
                is_red_flower TINYINT(1) DEFAULT 0 COMMENT '是否已求小红花',
                INDEX idx_owner_id (owner_id),
                INDEX idx_order_no (order_no),
                INDEX idx_account_id (account_id),
                INDEX idx_order_created_at (created_at),
                INDEX idx_order_placed_status (placed_at, status),
                INDEX idx_order_created_status (created_at, status),
                INDEX idx_order_owner_placed (owner_id, placed_at),
                INDEX idx_order_owner_created (owner_id, created_at),
                INDEX idx_order_owner_account_placed (owner_id, account_id, placed_at),
                INDEX idx_order_owner_account_buyer_created (owner_id, account_id, buyer_id, created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='订单表';

-- [8] xy_cards
CREATE TABLE IF NOT EXISTS xy_cards (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '卡券ID',
                user_id BIGINT NOT NULL COMMENT '所属用户ID',
                item_id VARCHAR(64) COMMENT '关联商品ID',
                name VARCHAR(255) NOT NULL COMMENT '卡券名称',
                type VARCHAR(50) NOT NULL COMMENT '卡券类型(api/text/data/image)',
                description TEXT COMMENT '卡券描述',
                enabled TINYINT(1) DEFAULT 1 COMMENT '是否启用',
                delay_seconds INT DEFAULT 0 COMMENT '延迟秒数',
                delivery_count INT DEFAULT 0 COMMENT '发货次数',
                price VARCHAR(32) COMMENT '对接价格',
                is_dockable TINYINT(1) DEFAULT 0 COMMENT '是否可对接',
                fee_payer VARCHAR(32) COMMENT '手续费支付方式：distributor-分销主支付，dealer-分销商支付',
                is_multi_spec TINYINT(1) DEFAULT 0 COMMENT '是否多规格',
                spec_name VARCHAR(255) COMMENT '规格名称',
                spec_value VARCHAR(255) COMMENT '规格值',
                api_config TEXT COMMENT 'API配置(JSON)',
                text_content TEXT COMMENT '文本内容',
                data_content TEXT COMMENT '数据内容',
                image_url VARCHAR(512) COMMENT '图片URL',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                image_urls TEXT COMMENT '多图片URL列表(JSON数组，最多3张)',
                min_price VARCHAR(32) COMMENT '最低售价',
                dock_visibility VARCHAR(32) DEFAULT NULL COMMENT '对接可见性：public-所有人可见，dealer_only-仅分销商可见',
                INDEX idx_user_id (user_id),
                INDEX idx_item_id (item_id),
                INDEX idx_card_user_item (user_id, item_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='卡券表';

-- [9] xy_default_replies
CREATE TABLE IF NOT EXISTS xy_default_replies (
                id INT PRIMARY KEY AUTO_INCREMENT COMMENT '回复ID',
                account_id VARCHAR(80) NOT NULL COMMENT '账号标识',
                item_id VARCHAR(64) DEFAULT NULL COMMENT '商品ID(空为账号默认回复)',
                enabled TINYINT(1) DEFAULT 0 COMMENT '是否启用',
                reply_content TEXT COMMENT '回复内容',
                reply_image VARCHAR(512) COMMENT '回复图片URL',
                reply_once TINYINT(1) DEFAULT 0 COMMENT '只回复一次',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_account_id (account_id),
                INDEX idx_item_id (item_id),
                UNIQUE KEY uk_account_item (account_id, item_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='默认回复表';

-- [10] xy_default_reply_records
CREATE TABLE IF NOT EXISTS xy_default_reply_records (
                id INT PRIMARY KEY AUTO_INCREMENT COMMENT '记录ID',
                account_id VARCHAR(80) NOT NULL COMMENT '账号标识',
                item_id VARCHAR(64) DEFAULT NULL COMMENT '商品ID(空为账号默认回复)',
                user_id VARCHAR(64) NOT NULL COMMENT '被回复用户ID',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                INDEX idx_account_id (account_id),
                INDEX idx_user_id (user_id),
                INDEX idx_account_item_user (account_id, item_id, user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='默认回复记录表';

-- [11] xy_ai_chat_messages
CREATE TABLE IF NOT EXISTS xy_ai_chat_messages (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '消息ID',
                chat_id VARCHAR(64) NOT NULL COMMENT '聊天ID',
                cookie_id VARCHAR(80) NOT NULL COMMENT '账号标识',
                user_id VARCHAR(64) NOT NULL COMMENT '用户ID',
                item_id VARCHAR(64) COMMENT '商品ID',
                role VARCHAR(20) NOT NULL COMMENT '角色(user/assistant)',
                content TEXT NOT NULL COMMENT '消息内容',
                intent VARCHAR(20) COMMENT '意图(price/tech/default)',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                INDEX idx_chat_id (chat_id),
                INDEX idx_cookie_id (cookie_id),
                INDEX ix_ai_chat_messages_chat_cookie (chat_id, cookie_id),
                INDEX ix_ai_chat_messages_intent (cookie_id, intent)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI聊天消息表';

-- [12] xy_risk_control_logs
CREATE TABLE IF NOT EXISTS xy_risk_control_logs (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '日志ID',
                owner_id BIGINT COMMENT '所属用户ID',
                account_id BIGINT COMMENT '关联账号ID',
                account_identifier VARCHAR(80) COMMENT '账号标识',
                event_type VARCHAR(64) DEFAULT 'slider_captcha' COMMENT '事件类型',
                event_description TEXT COMMENT '事件描述',
                processing_result TEXT COMMENT '处理结果',
                processing_status VARCHAR(32) DEFAULT 'processing' COMMENT '处理状态',
                error_message TEXT COMMENT '错误信息',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_owner_id (owner_id),
                INDEX idx_account_id (account_id),
                INDEX idx_event_type (event_type),
                INDEX idx_rcl_account_status (account_id, processing_status),
                INDEX idx_rcl_identifier_status_created (account_identifier, processing_status, created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='风控日志表';

-- [13] xy_account_login_logs
CREATE TABLE IF NOT EXISTS xy_account_login_logs (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '日志ID',
                owner_id BIGINT COMMENT '所属用户ID',
                account_id BIGINT COMMENT '关联账号ID（xy_accounts.id）',
                account_identifier VARCHAR(80) COMMENT '业务账号ID',
                username VARCHAR(255) COMMENT '登录用户名快照',
                trigger_reason VARCHAR(128) COMMENT '触发本次登录的原因',
                login_status VARCHAR(32) DEFAULT 'failed' COMMENT '登录状态：success/failed/skipped_cooldown/no_credentials',
                failure_reason VARCHAR(64) COMMENT '失败大类：bad_credentials/baxia_punish_captcha/account_info_missing/exception/...',
                error_message TEXT COMMENT '详细错误消息',
                updated_cookie_names VARCHAR(500) DEFAULT NULL COMMENT '接口续期更新的Cookie字段名（逗号分隔）',
                duration_ms INT COMMENT '整个登录流程耗时（毫秒）',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                INDEX idx_all_owner_id (owner_id),
                INDEX idx_all_account_id (account_id),
                INDEX idx_all_login_status (login_status),
                INDEX idx_all_identifier_status_created (account_identifier, login_status, created_at),
                INDEX idx_all_owner_created (owner_id, created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='账号登录日志表';

-- [14] xy_notification_channels
CREATE TABLE IF NOT EXISTS xy_notification_channels (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '渠道ID',
                owner_id BIGINT NOT NULL COMMENT '所属用户ID',
                name VARCHAR(120) NOT NULL COMMENT '渠道名称',
                channel_type VARCHAR(32) NOT NULL COMMENT '渠道类型',
                config JSON COMMENT '渠道配置',
                enabled TINYINT(1) DEFAULT 1 COMMENT '是否启用',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_owner_id (owner_id),
                INDEX idx_channel_type (channel_type)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通知渠道表';

-- [15] xy_message_notifications
CREATE TABLE IF NOT EXISTS xy_message_notifications (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '通知ID',
                owner_id BIGINT NOT NULL COMMENT '所属用户ID',
                account_pk BIGINT NOT NULL COMMENT '关联账号ID',
                account_identifier VARCHAR(80) NOT NULL COMMENT '账号标识',
                channel_id BIGINT NOT NULL COMMENT '渠道ID',
                enabled TINYINT(1) DEFAULT 1 COMMENT '是否启用',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_owner_id (owner_id),
                INDEX idx_account_pk (account_pk),
                INDEX idx_channel_id (channel_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='消息通知表';

-- [16] xy_message_filters
CREATE TABLE IF NOT EXISTS xy_message_filters (
                id INT PRIMARY KEY AUTO_INCREMENT COMMENT '规则ID',
                account_id VARCHAR(80) NOT NULL COMMENT '账号标识',
                keyword VARCHAR(255) NOT NULL COMMENT '过滤关键词',
                filter_type VARCHAR(20) NOT NULL COMMENT '过滤类型',
                enabled TINYINT(1) DEFAULT 1 COMMENT '是否启用',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_account_id (account_id),
                INDEX idx_keyword (keyword),
                UNIQUE KEY uk_account_keyword_type (account_id, keyword, filter_type)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='消息过滤规则表';

-- [17] xy_feedbacks
CREATE TABLE IF NOT EXISTS xy_feedbacks (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '反馈ID',
                user_id BIGINT NOT NULL COMMENT '用户ID',
                cookie_id VARCHAR(64) COMMENT '关联账号ID',
                title VARCHAR(100) NOT NULL COMMENT '标题',
                content TEXT NOT NULL COMMENT '内容',
                feedback_type ENUM('FEATURE', 'BUG', 'OTHER') DEFAULT 'OTHER' COMMENT '反馈类型',
                images TEXT COMMENT '图片URL(JSON数组)',
                is_resolved TINYINT(1) DEFAULT 0 COMMENT '是否已解决',
                resolved_at DATETIME COMMENT '解决时间',
                admin_reply TEXT COMMENT '管理员回复',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_user_id (user_id),
                INDEX idx_is_resolved (is_resolved),
                INDEX idx_feedback_type (feedback_type)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='意见反馈表';

-- [18] xy_feedback_messages
CREATE TABLE IF NOT EXISTS xy_feedback_messages (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '消息ID',
                feedback_id BIGINT NOT NULL COMMENT '关联反馈ID',
                user_id BIGINT NOT NULL COMMENT '发送者用户ID',
                content TEXT NOT NULL COMMENT '消息内容',
                is_admin TINYINT(1) DEFAULT 0 COMMENT '是否为管理员消息',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_feedback_id (feedback_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='意见反馈消息表';

-- [19] xy_advertisements
CREATE TABLE IF NOT EXISTS xy_advertisements (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '广告ID',
                user_id BIGINT NOT NULL COMMENT '申请用户ID',
                title VARCHAR(200) NOT NULL COMMENT '广告标题',
                content TEXT COMMENT '广告正文',
                link VARCHAR(500) COMMENT '广告链接',
                expire_date DATE COMMENT '到期日期',
                image_url VARCHAR(500) COMMENT '图片URL',
                ad_type ENUM('carousel', 'text') DEFAULT 'text' COMMENT '广告类型',
                months INT COMMENT '购买月数',
                total_amount VARCHAR(32) COMMENT '广告总金额',
                status ENUM('unpaid', 'pending', 'approved') DEFAULT 'unpaid' COMMENT '审核状态',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_user_id (user_id),
                INDEX idx_status (status),
                INDEX idx_ad_type (ad_type),
                INDEX idx_expire_date (expire_date)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='广告表';

-- [20] xy_goofish_crawl_jobs
CREATE TABLE IF NOT EXISTS xy_goofish_crawl_jobs (
                id BIGINT PRIMARY KEY AUTO_INCREMENT,
                owner_id BIGINT NOT NULL,
                cookie_id VARCHAR(80) NOT NULL,
                keyword VARCHAR(80) NOT NULL,
                interval_seconds INT NOT NULL DEFAULT 900,
                start_page INT NOT NULL DEFAULT 1,
                pages INT NOT NULL DEFAULT 1,
                page_size INT NOT NULL DEFAULT 20,
                fetch_detail TINYINT(1) DEFAULT 1,
                detail_limit INT NOT NULL DEFAULT 20,
                enabled TINYINT(1) DEFAULT 1,
                last_run_at DATETIME,
                last_error TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_owner_id (owner_id),
                INDEX idx_cookie_id (cookie_id),
                INDEX idx_enabled (enabled)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- [21] xy_goofish_crawl_items
CREATE TABLE IF NOT EXISTS xy_goofish_crawl_items (
                id BIGINT PRIMARY KEY AUTO_INCREMENT,
                job_id BIGINT NOT NULL,
                item_id VARCHAR(64) NOT NULL,
                title TEXT,
                price VARCHAR(64),
                area VARCHAR(120),
                seller_name VARCHAR(120),
                item_url TEXT,
                main_image VARCHAR(512),
                publish_time VARCHAR(64),
                want_count INT,
                view_count INT,
                description TEXT,
                detail_error VARCHAR(255),
                raw_json JSON,
                fetched_at DATETIME NOT NULL,
                UNIQUE KEY uk_job_item (job_id, item_id),
                INDEX idx_job_id (job_id),
                INDEX idx_fetched_at (fetched_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- [22] xy_scheduled_redelivery_log
CREATE TABLE IF NOT EXISTS `xy_scheduled_redelivery_log` (
                `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
                `batch_id` VARCHAR(36) NOT NULL COMMENT '批次ID',
                `account_id` VARCHAR(80) NOT NULL COMMENT '账号ID',
                `order_no` VARCHAR(64) NOT NULL COMMENT '订单号',
                `status` VARCHAR(20) NOT NULL COMMENT '状态',
                `error_message` VARCHAR(500) DEFAULT NULL COMMENT '错误信息',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                PRIMARY KEY (`id`),
                INDEX `idx_batch_id` (`batch_id`),
                INDEX `idx_account_id` (`account_id`),
                INDEX `idx_created_at` (`created_at`),
                INDEX `idx_srl_created_batch` (`created_at`, `batch_id`),
                INDEX `idx_srl_batch_created_status` (`batch_id`, `created_at`, `status`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='定时补发货执行日志表';

-- [23] xy_announcements
CREATE TABLE IF NOT EXISTS xy_announcements (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '公告ID',
                title VARCHAR(200) NOT NULL COMMENT '公告标题',
                content TEXT NOT NULL COMMENT '公告内容',
                is_deleted TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否已删除',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='公告信息表';

-- [24] xy_confirm_receipt_messages
CREATE TABLE IF NOT EXISTS xy_confirm_receipt_messages (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
                account_id VARCHAR(80) NOT NULL COMMENT '账号ID',
                enabled TINYINT(1) DEFAULT 0 COMMENT '是否启用',
                message_content TEXT COMMENT '消息文本内容',
                message_image VARCHAR(512) COMMENT '消息图片URL',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                UNIQUE KEY uk_account_id (account_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='确认收货消息配置表';

-- [25] xy_auto_rate_configs
CREATE TABLE IF NOT EXISTS xy_auto_rate_configs (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
                account_id VARCHAR(80) NOT NULL COMMENT '账号ID',
                enabled TINYINT(1) DEFAULT 0 COMMENT '是否启用自动评价',
                rate_type VARCHAR(20) DEFAULT 'text' COMMENT '评价类型',
                text_content TEXT COMMENT '固定评价文字内容',
                api_url VARCHAR(512) COMMENT 'API地址',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                UNIQUE KEY uk_account_id (account_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='自动评价配置表';

-- [26] xy_scheduled_rate_log
CREATE TABLE IF NOT EXISTS `xy_scheduled_rate_log` (
                `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
                `batch_id` VARCHAR(36) NOT NULL COMMENT '批次ID',
                `account_id` VARCHAR(80) NOT NULL COMMENT '账号ID',
                `order_no` VARCHAR(64) NOT NULL COMMENT '订单号',
                `status` VARCHAR(20) NOT NULL COMMENT '状态',
                `error_message` VARCHAR(500) DEFAULT NULL COMMENT '错误信息',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                PRIMARY KEY (`id`),
                INDEX `idx_batch_id` (`batch_id`),
                INDEX `idx_account_id` (`account_id`),
                INDEX `idx_created_at` (`created_at`),
                INDEX `idx_srate_created_batch` (`created_at`, `batch_id`),
                INDEX `idx_srate_batch_created_status` (`batch_id`, `created_at`, `status`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='定时补评价执行日志表';

-- [27] xy_scheduled_polish_log
CREATE TABLE IF NOT EXISTS `xy_scheduled_polish_log` (
                `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
                `batch_id` VARCHAR(36) NOT NULL COMMENT '批次ID',
                `account_id` VARCHAR(80) NOT NULL COMMENT '账号ID',
                `item_id` VARCHAR(64) NOT NULL COMMENT '商品ID',
                `status` VARCHAR(20) NOT NULL COMMENT '状态',
                `error_message` VARCHAR(500) DEFAULT NULL COMMENT '错误信息',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                PRIMARY KEY (`id`),
                INDEX `idx_batch_id` (`batch_id`),
                INDEX `idx_account_id` (`account_id`),
                INDEX `idx_created_at` (`created_at`),
                INDEX `idx_spol_created_batch` (`created_at`, `batch_id`),
                INDEX `idx_spol_batch_created_status` (`batch_id`, `created_at`, `status`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='定时擦亮执行日志表';

-- [28] xy_scheduled_login_renew_log
CREATE TABLE IF NOT EXISTS `xy_scheduled_login_renew_log` (
                `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
                `batch_id` VARCHAR(36) NOT NULL COMMENT '批次ID',
                `account_id` VARCHAR(80) NOT NULL COMMENT '账号ID',
                `status` VARCHAR(20) NOT NULL COMMENT '状态：success/token_refreshed/session_expired/failed',
                `error_message` VARCHAR(500) DEFAULT NULL COMMENT '错误信息或处理说明',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                PRIMARY KEY (`id`),
                INDEX `idx_batch_id` (`batch_id`),
                INDEX `idx_account_id` (`account_id`),
                INDEX `idx_created_at` (`created_at`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='登录续期执行日志表';

-- [29] xy_cookie_refresh_schedules
CREATE TABLE IF NOT EXISTS `xy_cookie_refresh_schedules` (
                `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
                `account_id` VARCHAR(80) NOT NULL COMMENT '账号ID',
                `expire_at` DATETIME NOT NULL COMMENT '当前Cookie续期到期时间',
                `last_refresh_at` DATETIME DEFAULT NULL COMMENT '最近一次续期成功时间',
                `last_status` VARCHAR(20) DEFAULT NULL COMMENT '最近一次状态：initialized/success/failed',
                `last_error_message` VARCHAR(500) DEFAULT NULL COMMENT '最近一次错误信息',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                PRIMARY KEY (`id`),
                UNIQUE KEY `uk_account_id` (`account_id`),
                INDEX `idx_expire_at` (`expire_at`),
                INDEX `idx_created_at` (`created_at`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Cookie续期计划表';

-- [30] xy_scheduled_cookies_refresh_log
CREATE TABLE IF NOT EXISTS `xy_scheduled_cookies_refresh_log` (
                `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
                `batch_id` VARCHAR(36) NOT NULL COMMENT '批次ID',
                `account_id` VARCHAR(80) NOT NULL COMMENT '账号ID',
                `status` VARCHAR(20) NOT NULL COMMENT '状态：initialized/success/failed',
                `updated_cookie_count` INT NOT NULL DEFAULT 0 COMMENT '本次增量更新的Cookie字段数量',
                `next_expire_at` DATETIME DEFAULT NULL COMMENT '下次到期时间',
                `error_message` VARCHAR(500) DEFAULT NULL COMMENT '错误信息或处理说明',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                PRIMARY KEY (`id`),
                INDEX `idx_batch_id` (`batch_id`),
                INDEX `idx_account_id` (`account_id`),
                INDEX `idx_status` (`status`),
                INDEX `idx_created_at` (`created_at`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='COOKIES刷新日志表';

-- [31] xy_scheduled_api_cookie_renew_log
CREATE TABLE IF NOT EXISTS `xy_scheduled_api_cookie_renew_log` (
                `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
                `batch_id` VARCHAR(36) NOT NULL COMMENT '批次ID，标识一次定时任务执行',
                `account_id` VARCHAR(80) NOT NULL COMMENT '账号ID',
                `status` VARCHAR(30) NOT NULL COMMENT '状态：success/cookie_updated/browser_renewed/need_password_login/failed',
                `updated_cookie_count` INT NOT NULL DEFAULT 0 COMMENT '本次更新的Cookie字段数量',
                `updated_cookie_names` TEXT DEFAULT NULL COMMENT '本次更新的Cookie字段名列表（逗号分隔）',
                `response_content` TEXT DEFAULT NULL COMMENT '接口返回内容（用于失败排查），最大裁剪到2000字符',
                `error_message` VARCHAR(500) DEFAULT NULL COMMENT '错误信息或处理说明',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                PRIMARY KEY (`id`),
                INDEX `idx_batch_id` (`batch_id`),
                INDEX `idx_account_id` (`account_id`),
                INDEX `idx_status` (`status`),
                INDEX `idx_created_at` (`created_at`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='接口续期Cookies执行日志表';

-- [32] xy_scheduled_tasks
CREATE TABLE IF NOT EXISTS `xy_scheduled_tasks` (
                `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
                `task_code` VARCHAR(50) NOT NULL COMMENT '任务代码',
                `task_name` VARCHAR(100) NOT NULL COMMENT '任务名称',
                `interval_seconds` INT NOT NULL DEFAULT 60 COMMENT '执行间隔(秒)',
                `enabled` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
                `description` TEXT COMMENT '任务描述',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                PRIMARY KEY (`id`),
                UNIQUE KEY `uk_task_code` (`task_code`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='定时任务配置表';

-- [33] xy_card_item_relations
CREATE TABLE IF NOT EXISTS xy_card_item_relations (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
                user_id BIGINT NOT NULL COMMENT '所属用户ID',
                card_id BIGINT NOT NULL COMMENT '卡券ID',
                item_id VARCHAR(64) NOT NULL COMMENT '商品ID',
                source VARCHAR(20) DEFAULT 'own' COMMENT '卡券来源：own-自有，dock_l1-一级对接，dock_l2-二级对接',
                dock_record_id BIGINT NOT NULL DEFAULT 0 COMMENT '对接记录ID（对接卡券时关联，0表示自有卡券）',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_user_id (user_id),
                INDEX idx_card_id (card_id),
                INDEX idx_item_id (item_id),
                INDEX idx_cir_user_item (user_id, item_id),
                UNIQUE KEY uk_card_item_dock (card_id, item_id, dock_record_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='卡券商品关联表';

-- [34] xy_dock_records
CREATE TABLE IF NOT EXISTS xy_dock_records (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
                user_id BIGINT NOT NULL COMMENT '用户ID',
                card_id BIGINT NOT NULL COMMENT '来源卡券ID',
                dock_name VARCHAR(255) NOT NULL COMMENT '对接名称',
                markup_amount VARCHAR(32) NOT NULL DEFAULT '0.00' COMMENT '加价金额',
                remark TEXT COMMENT '备注',
                delivery_count INT NOT NULL DEFAULT 0 COMMENT '发货次数',
                status TINYINT(1) DEFAULT 1 COMMENT '对接状态：1启用 0停用',
                disable_reason VARCHAR(255) DEFAULT NULL COMMENT '禁用原因',
                level INT NOT NULL DEFAULT 1 COMMENT '分销层级：1=一级分销，2=二级分销',
                parent_dock_id BIGINT DEFAULT NULL COMMENT '上级对接记录ID，一级分销为NULL',
                source_user_id BIGINT DEFAULT NULL COMMENT '上级分销商用户ID，一级分销为NULL',
                allow_sub_dock TINYINT(1) DEFAULT 0 COMMENT '是否允许下级对接',
                sub_dock_price VARCHAR(32) DEFAULT NULL COMMENT '给下级的对接价格（一级分销商设定）',
                sub_dock_visibility VARCHAR(32) DEFAULT NULL COMMENT '下级对接可见性：public-所有人可见，dealer_only-仅绑定对接码的分销商可见',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_user_id (user_id),
                INDEX idx_card_id (card_id),
                INDEX idx_parent_dock_id (parent_dock_id),
                INDEX idx_dock_user_level (user_id, level)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对接记录表';

-- [35] xy_fund_flows
CREATE TABLE IF NOT EXISTS xy_fund_flows (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
                user_id BIGINT NOT NULL COMMENT '用户ID',
                type VARCHAR(32) NOT NULL COMMENT '流水类型：income-收入，expense-支出',
                amount VARCHAR(32) NOT NULL COMMENT '发生额',
                balance_before VARCHAR(32) NOT NULL COMMENT '发生前余额',
                balance_after VARCHAR(32) NOT NULL COMMENT '发生后余额',
                order_id BIGINT DEFAULT NULL COMMENT '关联订单ID',
                dock_record_id BIGINT DEFAULT NULL COMMENT '关联对接记录ID',
                description VARCHAR(500) DEFAULT NULL COMMENT '流水描述',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '发生时间',
                INDEX idx_user_id (user_id),
                INDEX idx_order_id (order_id),
                INDEX idx_dock_record_id (dock_record_id),
                INDEX idx_created_at (created_at),
                INDEX idx_ff_user_id_desc (user_id, id),
                INDEX idx_ff_user_type_id_desc (user_id, type, id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='资金流水表';

-- [36] xy_recharge_orders
CREATE TABLE IF NOT EXISTS xy_recharge_orders (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
                order_no VARCHAR(64) NOT NULL COMMENT '充值订单号',
                user_id BIGINT NOT NULL COMMENT '用户ID',
                amount VARCHAR(32) NOT NULL COMMENT '充值金额',
                status VARCHAR(32) NOT NULL DEFAULT 'pending' COMMENT '订单状态：pending-待支付，paid-已支付，expired-已过期，failed-失败',
                trade_no VARCHAR(128) DEFAULT NULL COMMENT '支付宝交易号',
                qr_code VARCHAR(512) DEFAULT NULL COMMENT '支付二维码内容',
                paid_at DATETIME DEFAULT NULL COMMENT '支付时间',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                UNIQUE INDEX idx_order_no (order_no),
                INDEX idx_user_id (user_id),
                INDEX idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='充值订单表';

-- [37] xy_dock_code_bindings
CREATE TABLE IF NOT EXISTS xy_dock_code_bindings (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
                user_id BIGINT NOT NULL COMMENT '绑定用户ID（分销商）',
                dock_code VARCHAR(32) NOT NULL COMMENT '对接码',
                target_user_id BIGINT NOT NULL COMMENT '对接码拥有者用户ID（供应商）',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '绑定时间',
                UNIQUE INDEX uq_user_target (user_id, target_user_id),
                INDEX idx_user_id (user_id),
                INDEX idx_target_user_id (target_user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对接码绑定表';

-- [38] xy_agent_orders
CREATE TABLE IF NOT EXISTS xy_agent_orders (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
                user_id BIGINT NOT NULL COMMENT '下单用户ID（发货方）',
                order_no VARCHAR(64) NOT NULL COMMENT '闲鱼订单号',
                item_id VARCHAR(64) NOT NULL COMMENT '商品ID',
                card_id BIGINT NOT NULL COMMENT '使用的卡券ID',
                dock_record_id BIGINT NOT NULL COMMENT '对接记录ID',
                dock_level INT NOT NULL COMMENT '对接层级：1=一级，2=二级',
                sale_price VARCHAR(32) NOT NULL COMMENT '售价（用户卖出的价格）',
                dock_price VARCHAR(32) NOT NULL COMMENT '对接价格（拿货价）',
                card_price VARCHAR(32) DEFAULT NULL COMMENT '卡券成本（货主对接价）',
                level2_cost VARCHAR(32) DEFAULT NULL COMMENT '二级拿货价（一级的sub_dock_price）',
                profit VARCHAR(32) NOT NULL DEFAULT '0.00' COMMENT '利润（售价-对接价）',
                fee_amount VARCHAR(32) DEFAULT NULL COMMENT '手续费金额',
                fee_payer VARCHAR(32) DEFAULT NULL COMMENT '手续费承担方：dealer-分销商，distributor-货主',
                upstream_user_id BIGINT DEFAULT NULL COMMENT '上级用户ID',
                upstream_dock_record_id BIGINT DEFAULT NULL COMMENT '上级对接记录ID',
                owner_user_id BIGINT DEFAULT NULL COMMENT '货主用户ID',
                delivery_content TEXT COMMENT '发货内容',
                buyer_id VARCHAR(64) DEFAULT NULL COMMENT '买家ID',
                status VARCHAR(32) NOT NULL DEFAULT 'delivered' COMMENT '状态：delivered-已发货，settled-已结算，failed-失败',
                settle_remark VARCHAR(500) DEFAULT NULL COMMENT '结算备注',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_user_id (user_id),
                INDEX idx_order_no (order_no),
                INDEX idx_dock_record_id (dock_record_id),
                INDEX idx_upstream_user_id (upstream_user_id),
                INDEX idx_status (status),
                INDEX idx_agent_order_created (created_at),
                INDEX idx_ao_upstream_status (upstream_user_id, status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='代理订单表';

-- [39] xy_token_cache
CREATE TABLE IF NOT EXISTS xy_token_cache (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
                user_id VARCHAR(128) NOT NULL COMMENT '用户ID（myid）',
                token TEXT NOT NULL COMMENT 'IM Token',
                device_id VARCHAR(128) NOT NULL COMMENT '设备ID',
                expire_at DATETIME NOT NULL COMMENT '过期时间',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                UNIQUE KEY uk_user_id (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Token缓存表';

-- [40] xy_settlement_records
CREATE TABLE IF NOT EXISTS xy_settlement_records (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
                user_id BIGINT NOT NULL COMMENT '用户ID',
                alipay_id VARCHAR(128) NOT NULL COMMENT '支付宝ID',
                amount VARCHAR(32) NOT NULL COMMENT '提现金额',
                status VARCHAR(32) NOT NULL DEFAULT 'pending_review' COMMENT '状态：pending_review-待审核，approved-已通过，rejected-已拒绝，paid-已打款',
                remark TEXT COMMENT '备注',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                payment_type VARCHAR(16) COMMENT '收款方式：alipay-支付宝，wechat-微信',
                payment_qrcode VARCHAR(512) COMMENT '收款码图片路径',
                reject_reason VARCHAR(512) COMMENT '拒绝原因',
                INDEX idx_user_id (user_id),
                INDEX idx_status (status),
                INDEX idx_created_at (created_at),
                INDEX idx_sr_user_created_id (user_id, created_at, id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='结算记录表';

-- [41] xy_activation_logs
CREATE TABLE IF NOT EXISTS xy_activation_logs (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
                machine_id VARCHAR(32) NOT NULL COMMENT '机器码',
                code_type VARCHAR(20) NOT NULL COMMENT '类型：generate-获取激活码，renew-续期码',
                generated_code VARCHAR(255) NOT NULL COMMENT '生成的激活码/续期码',
                days INT NOT NULL COMMENT '有效天数',
                ip_address VARCHAR(64) COMMENT '请求IP地址',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间（北京时间）',
                INDEX idx_machine_id (machine_id),
                INDEX idx_code_type (code_type),
                INDEX idx_machine_type_time (machine_id, code_type, created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='激活码生成日志表';

-- [42] xy_product_materials
CREATE TABLE IF NOT EXISTS xy_product_materials (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
                user_id BIGINT NOT NULL COMMENT '所属用户ID',
                title VARCHAR(200) NOT NULL COMMENT '商品标题',
                description TEXT NOT NULL COMMENT '商品描述',
                price DECIMAL(12,2) NOT NULL COMMENT '价格',
                original_price DECIMAL(12,2) DEFAULT NULL COMMENT '原价（划线价）',
                category VARCHAR(100) DEFAULT NULL COMMENT '商品分类',
                images JSON DEFAULT NULL COMMENT '图片URL列表（最多9张）',
                delivery_method VARCHAR(20) DEFAULT 'express' COMMENT '发货方式：express-快递, pickup-自提',
                postage DECIMAL(8,2) DEFAULT 0 COMMENT '邮费，0表示包邮',
                address VARCHAR(200) DEFAULT NULL COMMENT '宝贝所在地',
                brand VARCHAR(100) DEFAULT NULL COMMENT '品牌',
                `condition` VARCHAR(20) DEFAULT '全新' COMMENT '成色',
                remark VARCHAR(500) DEFAULT NULL COMMENT '备注（仅内部使用）',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_user_id (user_id),
                INDEX idx_created_at (created_at),
                INDEX idx_pm_user_created (user_id, created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='商品素材库表';

-- [43] xy_scheduled_red_flower_log
CREATE TABLE IF NOT EXISTS `xy_scheduled_red_flower_log` (
                `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
                `batch_id` VARCHAR(36) NOT NULL COMMENT '批次ID',
                `account_id` VARCHAR(80) NOT NULL COMMENT '账号ID',
                `order_no` VARCHAR(64) NOT NULL COMMENT '订单号',
                `status` VARCHAR(20) NOT NULL COMMENT '状态：success/failed',
                `error_message` VARCHAR(500) DEFAULT NULL COMMENT '错误信息',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                PRIMARY KEY (`id`),
                INDEX `idx_batch_id` (`batch_id`),
                INDEX `idx_account_id` (`account_id`),
                INDEX `idx_created_at` (`created_at`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='定时求小红花执行日志表';

-- [44] xy_scheduled_close_notice_log
CREATE TABLE IF NOT EXISTS `xy_scheduled_close_notice_log` (
                `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
                `batch_id` VARCHAR(36) NOT NULL COMMENT '批次ID',
                `account_id` VARCHAR(80) NOT NULL COMMENT '账号ID',
                `status` VARCHAR(20) NOT NULL COMMENT '状态：success/failed',
                `error_message` VARCHAR(500) DEFAULT NULL COMMENT '错误信息',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                PRIMARY KEY (`id`),
                INDEX `idx_batch_id` (`batch_id`),
                INDEX `idx_account_id` (`account_id`),
                INDEX `idx_created_at` (`created_at`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='账号消息通知关闭执行日志表';

-- [45] xy_auto_reply_message_logs
CREATE TABLE IF NOT EXISTS xy_auto_reply_message_logs (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
                owner_id BIGINT DEFAULT NULL COMMENT '所属系统用户ID',
                owner_username VARCHAR(120) DEFAULT NULL COMMENT '所属系统用户名',
                account_pk BIGINT DEFAULT NULL COMMENT '账号主键ID',
                account_id VARCHAR(80) NOT NULL COMMENT '闲鱼账号ID',
                account_name VARCHAR(120) DEFAULT NULL COMMENT '闲鱼账号显示名称',
                chat_id VARCHAR(128) NOT NULL COMMENT '聊天会话ID',
                item_id VARCHAR(64) DEFAULT NULL COMMENT '商品ID',
                item_title VARCHAR(255) DEFAULT NULL COMMENT '商品标题',
                source_message_id VARCHAR(128) DEFAULT NULL COMMENT '源消息ID',
                sender_user_id VARCHAR(64) NOT NULL COMMENT '发送方闲鱼用户ID',
                sender_user_name VARCHAR(120) DEFAULT NULL COMMENT '发送方昵称',
                source_message TEXT COMMENT '收到的消息内容',
                source_message_time DATETIME DEFAULT NULL COMMENT '收到消息时间',
                process_status VARCHAR(20) NOT NULL DEFAULT 'processing' COMMENT '处理状态：processing/success/skipped/failed',
                decision_reason VARCHAR(64) NOT NULL DEFAULT 'processing' COMMENT '决策原因',
                reply_strategy VARCHAR(20) NOT NULL DEFAULT 'none' COMMENT '回复策略：keyword/ai/default/none',
                reply_mode VARCHAR(20) NOT NULL DEFAULT 'none' COMMENT '回复模式：text/image/text_image/none',
                matched_keyword VARCHAR(255) DEFAULT NULL COMMENT '命中的关键词',
                matched_rule_type VARCHAR(32) DEFAULT NULL COMMENT '命中的规则类型',
                default_reply_scope VARCHAR(20) DEFAULT NULL COMMENT '默认回复作用域：item/account',
                default_reply_once TINYINT(1) NOT NULL DEFAULT 0 COMMENT '默认回复是否仅回复一次',
                ai_model_name VARCHAR(120) DEFAULT NULL COMMENT 'AI模型名称',
                ai_provider_name VARCHAR(80) DEFAULT NULL COMMENT 'AI服务商名称',
                reply_text TEXT COMMENT '回复文本内容',
                reply_image_url VARCHAR(1000) DEFAULT NULL COMMENT '回复图片URL',
                reply_segments JSON DEFAULT NULL COMMENT '拆分后的回复分段',
                error_message TEXT COMMENT '错误信息',
                raw_message_json JSON DEFAULT NULL COMMENT '原始消息JSON',
                context_snapshot JSON DEFAULT NULL COMMENT '上下文快照',
                send_result_json JSON DEFAULT NULL COMMENT '发送结果快照',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_owner_id (owner_id),
                INDEX idx_account_pk (account_pk),
                INDEX idx_account_id (account_id),
                INDEX idx_chat_id (chat_id),
                INDEX idx_item_id (item_id),
                INDEX idx_source_message_id (source_message_id),
                INDEX idx_sender_user_id (sender_user_id),
                INDEX idx_process_status (process_status),
                INDEX idx_decision_reason (decision_reason),
                INDEX idx_created_at (created_at),
                INDEX idx_arml_account_created (account_id, created_at),
                INDEX idx_arml_account_status_created (account_id, process_status, created_at),
                INDEX idx_arml_owner_created (owner_id, created_at),
                INDEX idx_arml_owner_status_created (owner_id, process_status, created_at),
                INDEX idx_arml_status_created (process_status, created_at),
                INDEX idx_arml_status_strategy_created (process_status, reply_strategy, created_at),
                INDEX idx_arml_strategy_created (reply_strategy, created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='自动回复消息日志表';

-- [46] xy_publish_addresses
CREATE TABLE IF NOT EXISTS xy_publish_addresses (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
                name VARCHAR(120) NOT NULL COMMENT '地址名称',
                search_keyword VARCHAR(200) NOT NULL COMMENT '地址搜索关键词',
                expected_text VARCHAR(200) DEFAULT NULL COMMENT '期望命中的候选文本',
                account_id VARCHAR(80) DEFAULT NULL COMMENT '限定使用的闲鱼账号ID，空表示全局通用',
                weight INT NOT NULL DEFAULT 1 COMMENT '随机权重',
                sort_order INT NOT NULL DEFAULT 100 COMMENT '排序值',
                is_enabled TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
                use_count INT NOT NULL DEFAULT 0 COMMENT '使用次数',
                last_used_at DATETIME DEFAULT NULL COMMENT '最后使用时间',
                created_by BIGINT DEFAULT NULL COMMENT '创建人用户ID',
                remark VARCHAR(500) DEFAULT NULL COMMENT '备注',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_account_id (account_id),
                INDEX idx_pa_enabled_account (is_enabled, account_id),
                INDEX idx_pa_sort_created (sort_order, created_at),
                UNIQUE KEY uk_search_keyword_account (search_keyword, account_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='商品发布随机地址池表';

-- [47] xy_publish_logs
CREATE TABLE IF NOT EXISTS xy_publish_logs (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
                user_id BIGINT NOT NULL COMMENT '操作用户ID',
                account_id VARCHAR(80) NOT NULL COMMENT '闲鱼账号ID（cookie_id）',
                title VARCHAR(200) NOT NULL COMMENT '商品标题',
                description TEXT DEFAULT NULL COMMENT '商品描述',
                price VARCHAR(20) DEFAULT NULL COMMENT '发布价格',
                material_id BIGINT DEFAULT NULL COMMENT '关联的素材ID（批量发布时使用）',
                batch_id VARCHAR(36) DEFAULT NULL COMMENT '批次ID（批量发布任务标识）',
                status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '状态：pending/publishing/success/failed',
                item_url VARCHAR(500) DEFAULT NULL COMMENT '发布成功后的商品链接',
                item_id VARCHAR(64) DEFAULT NULL COMMENT '发布成功后的商品ID',
                error_message VARCHAR(1000) DEFAULT NULL COMMENT '失败原因',
                resolved_address_id BIGINT DEFAULT NULL COMMENT '本次发布命中的地址池ID',
                resolved_address_text VARCHAR(200) DEFAULT NULL COMMENT '本次发布实际使用的地址搜索词',
                address_source VARCHAR(20) DEFAULT NULL COMMENT '地址来源：material/account_pool/global_pool',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_user_id (user_id),
                INDEX idx_account_id (account_id),
                INDEX idx_batch_id (batch_id),
                INDEX idx_status (status),
                INDEX idx_created_at (created_at),
                INDEX idx_publish_user_created (user_id, created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='商品发布日志表';

-- [48] xy_shared_scan_sessions
CREATE TABLE IF NOT EXISTS xy_shared_scan_sessions (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
                session_id VARCHAR(36) NOT NULL UNIQUE COMMENT '会话唯一ID（UUID）',
                owner_id BIGINT NOT NULL COMMENT '创建者用户ID',
                owner_username VARCHAR(120) NOT NULL COMMENT '创建者用户名',
                status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '会话状态：active/closed',
                expires_at DATETIME NOT NULL COMMENT '过期时间（默认72小时）',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_session_id (session_id),
                INDEX idx_owner_id (owner_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='共享扫码登录会话表';

-- [49] xy_delivery_block_rules
CREATE TABLE IF NOT EXISTS xy_delivery_block_rules (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
                account_id VARCHAR(64) NOT NULL COMMENT '账号ID',
                rule_code VARCHAR(50) NOT NULL COMMENT '规则编码',
                enabled TINYINT(1) NOT NULL DEFAULT 0 COMMENT '规则开关',
                priority INT NOT NULL DEFAULT 0 COMMENT '执行优先级（越小越先执行）',
                block_reason VARCHAR(500) DEFAULT NULL COMMENT '禁止发货原因（发给买家的消息）',
                auto_close_order TINYINT(1) NOT NULL DEFAULT 0 COMMENT '命中后主动关闭订单',
                only_card_after_close TINYINT(1) NOT NULL DEFAULT 0 COMMENT '关闭订单后继续发货（只发卡券）',
                excluded_item_ids JSON DEFAULT NULL COMMENT '该规则的排除商品列表（命中则跳过本规则）',
                config JSON DEFAULT NULL COMMENT '规则专属参数',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_account_id (account_id),
                UNIQUE KEY uk_account_rule (account_id, rule_code)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='禁止发货规则配置表';

-- [50] xy_shared_scan_workers
CREATE TABLE IF NOT EXISTS xy_shared_scan_workers (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
                shared_session_id VARCHAR(36) NOT NULL COMMENT '关联的共享会话ID',
                sub_session_id VARCHAR(36) NOT NULL UNIQUE COMMENT '兼职子会话唯一ID（UUID）',
                xianyu_session_id VARCHAR(36) DEFAULT NULL COMMENT '关联的闲鱼QR登录会话ID',
                status VARCHAR(20) NOT NULL DEFAULT 'qrcode_ready' COMMENT '状态：qrcode_ready/scanning/success/failed',
                qr_code_url LONGTEXT DEFAULT NULL COMMENT '二维码图片base64 data URL',
                account_id VARCHAR(80) DEFAULT NULL COMMENT '扫码成功后的闲鱼账号ID（unb）',
                cookie_saved TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Cookie是否已保存到账号表',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_shared_session_id (shared_session_id),
                INDEX idx_sub_session_id (sub_session_id),
                INDEX idx_account_id (account_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='共享扫码登录兼职工作者表';


-- ============================================================
-- 返佣系统表（fy_ 前缀）
-- ============================================================

-- [51] fy_accounts
CREATE TABLE IF NOT EXISTS fy_accounts (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
                owner_id BIGINT NOT NULL COMMENT '所属用户ID',
                account_id VARCHAR(80) NOT NULL COMMENT '账号标识',
                account_type ENUM('TAOBAO','JD','MEITUAN') DEFAULT 'TAOBAO' COMMENT '账号类型',
                display_name VARCHAR(120) COMMENT '显示名称',
                cookie TEXT NOT NULL COMMENT '账号Cookie',
                app_key VARCHAR(80) DEFAULT NULL COMMENT '淘宝开放平台AppKey',
                app_secret VARCHAR(200) DEFAULT NULL COMMENT '淘宝开放平台AppSecret',
                adzone_id VARCHAR(80) DEFAULT NULL COMMENT '淘宝推广位ID',
                enabled TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
                remark VARCHAR(255) COMMENT '备注',
                last_login_at DATETIME COMMENT '最后登录时间',
                disable_reason VARCHAR(255) COMMENT '禁用原因',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_fy_account_owner (owner_id),
                INDEX idx_fy_account_id (account_id),
                INDEX idx_fy_account_type (account_type),
                INDEX idx_fy_account_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='返佣系统推广账号表';

-- [52] fy_product_rules
CREATE TABLE IF NOT EXISTS fy_product_rules (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
                owner_id BIGINT NOT NULL COMMENT '所属用户ID',
                account_id VARCHAR(80) DEFAULT NULL COMMENT '闲鱼账号ID',
                rule_name VARCHAR(120) NOT NULL COMMENT '规则名称',
                cat VARCHAR(50) COMMENT '商品类目ID',
                cat_name VARCHAR(100) COMMENT '商品类目名称',
                keyword VARCHAR(200) COMMENT '商品关键词',
                sort VARCHAR(50) DEFAULT 'default' COMMENT '排序规则',
                daily_count INT NOT NULL DEFAULT 10 COMMENT '每天选品条数',
                enabled TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
                remark VARCHAR(255) COMMENT '备注',
                last_run_at DATETIME COMMENT '最后执行时间',
                last_run_date DATE COMMENT '最后执行日期',
                today_count INT NOT NULL DEFAULT 0 COMMENT '今天已选品数量',
                total_selected_count INT NOT NULL DEFAULT 0 COMMENT '累计选品数量',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_owner_id (owner_id),
                INDEX idx_account_id (account_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='返佣系统选品规则表';

-- [53] fy_materials
CREATE TABLE IF NOT EXISTS fy_materials (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
                owner_id BIGINT NOT NULL COMMENT '所属用户ID',
                account_id VARCHAR(80) DEFAULT NULL COMMENT '闲鱼账号ID',
                rule_id BIGINT DEFAULT NULL COMMENT '来源选品规则ID',
                item_id VARCHAR(50) NOT NULL COMMENT '淘宝商品ID',
                title VARCHAR(500) NOT NULL COMMENT '商品标题',
                price DECIMAL(10,2) NOT NULL DEFAULT 0.10 COMMENT '售价',
                stock INT NOT NULL DEFAULT 999 COMMENT '库存',
                description TEXT COMMENT '商品描述',
                images TEXT COMMENT '商品图片URL列表（JSON数组）',
                click_url VARCHAR(1000) COMMENT '推广链接',
                coupon_url VARCHAR(1000) COMMENT '券二合一推广链接',
                tpwd VARCHAR(200) COMMENT '淘口令',
                short_url VARCHAR(1000) COMMENT '短连接',
                original_price VARCHAR(20) COMMENT '商品原价',
                commission_rate VARCHAR(20) COMMENT '佣金率',
                commission_amount VARCHAR(20) COMMENT '佣金金额',
                promotion_price VARCHAR(20) COMMENT '到手价',
                coupon_info VARCHAR(255) COMMENT '优惠券信息',
                shop_title VARCHAR(200) COMMENT '店铺名称',
                volume VARCHAR(50) COMMENT '月销量',
                publish_status VARCHAR(20) NOT NULL DEFAULT 'unpublished' COMMENT '发布状态',
                published TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否已发布到闲鱼',
                published_at DATETIME COMMENT '发布时间',
                published_item_id VARCHAR(64) COMMENT '发布后闲鱼商品ID',
                publish_random_str VARCHAR(32) COMMENT '发布随机字符',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_fy_material_owner (owner_id),
                INDEX idx_fy_material_account (account_id),
                INDEX idx_fy_material_owner_account_publish_status (owner_id, account_id, publish_status),
                INDEX idx_fy_material_rule (rule_id),
                INDEX idx_fy_material_item (item_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='返佣系统素材库表';

-- [54] fy_publish_rules
CREATE TABLE IF NOT EXISTS fy_publish_rules (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
                owner_id BIGINT NOT NULL COMMENT '所属用户ID',
                rule_name VARCHAR(120) NOT NULL COMMENT '规则名称',
                account_id VARCHAR(80) NOT NULL COMMENT '闲鱼账号ID',
                daily_count INT NOT NULL DEFAULT 5 COMMENT '每天发布数量',
                enabled TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
                remark VARCHAR(255) COMMENT '备注',
                last_run_at DATETIME COMMENT '最后执行时间',
                last_run_date DATE COMMENT '最后执行日期',
                today_count INT NOT NULL DEFAULT 0 COMMENT '今天已发布数量',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_owner_id (owner_id),
                UNIQUE KEY uq_fy_publish_rules_owner_account (owner_id, account_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='返佣系统发布规则表';

-- [55] fy_delete_rules
CREATE TABLE IF NOT EXISTS fy_delete_rules (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
                owner_id BIGINT NOT NULL COMMENT '所属用户ID',
                rule_name VARCHAR(120) NOT NULL COMMENT '规则名称',
                account_id VARCHAR(80) NOT NULL COMMENT '闲鱼账号ID',
                daily_count INT NOT NULL DEFAULT 5 COMMENT '每天删除数量',
                min_publish_days INT NOT NULL DEFAULT 7 COMMENT '发布满多少天才能删除',
                enabled TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
                remark VARCHAR(255) COMMENT '备注',
                last_run_at DATETIME COMMENT '最后执行时间',
                last_run_date DATE COMMENT '最后执行日期',
                today_count INT NOT NULL DEFAULT 0 COMMENT '今天已删除数量',
                total_deleted_count INT NOT NULL DEFAULT 0 COMMENT '累计删除数量',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_owner_id (owner_id),
                UNIQUE KEY uq_fy_delete_rules_owner_account (owner_id, account_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='返佣系统删除规则表';

