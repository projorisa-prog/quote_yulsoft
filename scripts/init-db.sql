-- ==========================================
-- Yulsoft Quote - Database Initialization
-- ==========================================

-- UUID 확장 활성화
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 인덱스 생성 최적화를 위한 설정
SET maintenance_work_mem = '256MB';

-- 사용자 테이블 (애플리케이션에서 자동 생성되지만 초기 데이터용)
-- ALTER TABLE users ALTER COLUMN id SET DEFAULT uuid_generate_v4();

-- 기본 관리자 계정 (개발용)
-- 비밀번호: admin123 (bcrypt 해시)
-- INSERT INTO users (id, email, password_hash, company_name, ceo_name, biz_reg_no, plan, quote_seq, is_active, created_at)
-- VALUES (uuid_generate_v4(), 'admin@yulsoft.kr', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S', '율소프트', '김대표', '1234567890', 'ENTERPRISE', 0, true, NOW())
-- ON CONFLICT (email) DO NOTHING;

-- 기본 템플릿 데이터 (선택사항)

-- 통계용 뷰 생성 (나중에)

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- 완료 메시지
SELECT 'Database initialized successfully!' AS status;