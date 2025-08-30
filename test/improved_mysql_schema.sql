-- =====================================================
-- 개선된 시장 데이터 테이블 생성 스크립트 (MySQL)
-- 정규화된 구조 - RDS MySQL 서버용
-- =====================================================

-- =====================================================
-- 1. 마켓 인스트루먼트 마스터 테이블 생성
-- =====================================================
CREATE TABLE IF NOT EXISTS market_instruments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL COMMENT '^GSPC, USDKRW=X 등',
    name VARCHAR(100) NOT NULL COMMENT 'S&P 500, USD/KRW 등',
    market_type VARCHAR(20) NOT NULL COMMENT '상품 타입: STOCK_INDEX, CURRENCY, RATE 등',
    country VARCHAR(10) NOT NULL COMMENT '국가 코드: US, KR, GLOBAL 등',
    currency VARCHAR(3) NOT NULL COMMENT 'USD, KRW 등',
    description VARCHAR(200) DEFAULT NULL COMMENT '상품 설명',
    is_active VARCHAR(10) DEFAULT 'Yes' COMMENT '활성 상태',
    
    -- 데이터 무결성을 위한 CHECK 제약조건 (MySQL 8.0+)
    CONSTRAINT chk_market_type CHECK (market_type IN ('STOCK_INDEX', 'BOND_INDEX', 'COMMODITY', 'CURRENCY', 'RATE')),
    CONSTRAINT chk_country CHECK (country IN ('US', 'KR', 'GLOBAL')),
    CONSTRAINT chk_is_active CHECK (is_active IN ('Yes', 'No')),
    
    -- 인덱스
    INDEX idx_market_type (market_type),
    INDEX idx_country (country),
    INDEX idx_active (is_active),
    INDEX idx_symbol (symbol)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='마켓 인스트루먼트 마스터 테이블';

-- =====================================================
-- 2. 시장 가격 데이터 테이블 생성 (통합)
-- =====================================================
CREATE TABLE IF NOT EXISTS market_price_daily (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instrument_id INT NOT NULL COMMENT '마켓 인스트루먼트 ID',
    date DATE NOT NULL COMMENT '데이터 날짜',
    
    -- 가격 데이터
    open_price DECIMAL(20, 8) DEFAULT NULL COMMENT '시가',
    high_price DECIMAL(20, 8) DEFAULT NULL COMMENT '고가',
    low_price DECIMAL(20, 8) DEFAULT NULL COMMENT '저가',
    close_price DECIMAL(20, 8) NOT NULL COMMENT '종가',
    volume DECIMAL(20, 0) DEFAULT NULL COMMENT '거래량',
    
    -- 계산된 필드
    daily_return DECIMAL(10, 6) DEFAULT NULL COMMENT '일일 수익률 (%)',
    
    -- 외래키 및 제약조건
    FOREIGN KEY (instrument_id) REFERENCES market_instruments(id) ON DELETE CASCADE,
    UNIQUE KEY unique_instrument_date (instrument_id, date),
    
    -- 인덱스
    INDEX idx_instrument_id (instrument_id),
    INDEX idx_date (date),
    INDEX idx_instrument_date (instrument_id, date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='시장 가격 데이터 테이블 (통합)';

-- =====================================================
-- 3. 무위험 이자율 데이터 테이블 생성
-- =====================================================
CREATE TABLE IF NOT EXISTS risk_free_rate_daily (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instrument_id INT NOT NULL COMMENT '마켓 인스트루먼트 ID',
    date DATE NOT NULL COMMENT '데이터 날짜',
    rate DECIMAL(8, 4) NOT NULL COMMENT '이자율 (%)',
    rate_type VARCHAR(30) NOT NULL COMMENT '금리 유형: CENTRAL_BANK_RATE, TREASURY_RATE 등',
    
    -- 데이터 무결성을 위한 CHECK 제약조건
    CONSTRAINT chk_rate_type CHECK (rate_type IN ('CENTRAL_BANK_RATE', 'TREASURY_RATE', 'CORPORATE_BOND_RATE')),
    CONSTRAINT chk_rate_range CHECK (rate >= -10.0 AND rate <= 50.0),
    
    -- 외래키 및 제약조건
    FOREIGN KEY (instrument_id) REFERENCES market_instruments(id) ON DELETE CASCADE,
    UNIQUE KEY unique_rate_instrument_date (instrument_id, date),
    
    -- 인덱스
    INDEX idx_rate_instrument_id (instrument_id),
    INDEX idx_rate_date (date),
    INDEX idx_rate_type (rate_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='무위험 이자율 데이터 테이블';

-- =====================================================
-- 4. 초기 마켓 인스트루먼트 데이터 삽입
-- =====================================================

-- 미국 주식 지수
INSERT IGNORE INTO market_instruments (symbol, name, market_type, country, currency, description) VALUES 
('^GSPC', 'S&P 500', 'STOCK_INDEX', 'US', 'USD', 'Standard & Poor 500 Index'),
('^IXIC', 'NASDAQ Composite', 'STOCK_INDEX', 'US', 'USD', 'NASDAQ Composite Index');

-- 한국 주식 지수  
INSERT IGNORE INTO market_instruments (symbol, name, market_type, country, currency, description) VALUES
('^KS11', 'KOSPI', 'STOCK_INDEX', 'KR', 'KRW', '한국종합주가지수'),
('^KQ11', 'KOSDAQ', 'STOCK_INDEX', 'KR', 'KRW', '코스닥지수');

-- 환율
INSERT IGNORE INTO market_instruments (symbol, name, market_type, country, currency, description) VALUES
('USDKRW=X', 'USD/KRW', 'CURRENCY', 'GLOBAL', 'KRW', '달러원 환율');

-- 무위험 이자율
INSERT IGNORE INTO market_instruments (symbol, name, market_type, country, currency, description) VALUES
('^IRX', '3-Month Treasury Bill', 'RATE', 'US', 'USD', '미국 3개월 국채금리'),
('KOR_BASE_RATE', '한국은행 기준금리', 'RATE', 'KR', 'KRW', '한국은행 기준금리');

-- =====================================================
-- 5. 뷰 생성 (하위 호환성을 위한)
-- =====================================================

-- 벤치마크 지수 뷰 (기존 benchmark_indices 테이블 대체)
CREATE OR REPLACE VIEW benchmark_indices_view AS
SELECT 
    mpd.id,
    mi.symbol,
    mi.name,
    mi.country,
    mpd.date,
    mpd.close_price,
    mi.currency,
    mpd.daily_return
FROM market_price_daily mpd
JOIN market_instruments mi ON mpd.instrument_id = mi.id
WHERE mi.market_type = 'STOCK_INDEX' AND mi.is_active = 'Yes';

-- 환율 뷰 (기존 exchange_rates 테이블 대체)
CREATE OR REPLACE VIEW exchange_rates_view AS
SELECT 
    mpd.id,
    mi.symbol AS currency_pair,
    mpd.date,
    mpd.close_price AS close_rate,
    mpd.daily_return
FROM market_price_daily mpd
JOIN market_instruments mi ON mpd.instrument_id = mi.id
WHERE mi.market_type = 'CURRENCY' AND mi.is_active = 'Yes';

-- 무위험 이자율 뷰 (기존 risk_free_rates 테이블 대체)
CREATE OR REPLACE VIEW risk_free_rates_view AS
SELECT 
    rfd.id,
    mi.country,
    rfd.rate_type,
    mi.name,
    mi.symbol,
    rfd.date,
    rfd.rate,
    mi.currency
FROM risk_free_rate_daily rfd
JOIN market_instruments mi ON rfd.instrument_id = mi.id
WHERE mi.market_type = 'RATE' AND mi.is_active = 'Yes';

-- =====================================================
-- 6. 테이블 생성 확인 쿼리
-- =====================================================

-- 생성된 테이블 목록 확인
SELECT TABLE_NAME, TABLE_COMMENT 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = DATABASE() 
AND TABLE_NAME IN ('market_instruments', 'market_price_daily', 'risk_free_rate_daily')
ORDER BY TABLE_NAME;

-- 마켓 인스트루먼트 데이터 확인
SELECT id, symbol, name, market_type, country, currency 
FROM market_instruments 
ORDER BY market_type, country, symbol;

-- 생성된 뷰 확인
SELECT TABLE_NAME, TABLE_TYPE 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = DATABASE() 
AND TABLE_NAME LIKE '%_view'
ORDER BY TABLE_NAME;

-- =====================================================
-- 7. 성능 최적화를 위한 추가 인덱스 (선택사항)
-- =====================================================

-- 자주 사용되는 쿼리 패턴에 대한 복합 인덱스
-- ALTER TABLE market_price_daily ADD INDEX idx_date_instrument (date, instrument_id);
-- ALTER TABLE risk_free_rate_daily ADD INDEX idx_date_instrument (date, instrument_id);

-- =====================================================
-- 완료: 개선된 시장 데이터 테이블 생성 완료
-- =====================================================

-- 테이블별 레코드 수 확인 (데이터 수집 후)
-- SELECT 
--     'market_instruments' AS table_name, COUNT(*) AS record_count FROM market_instruments
-- UNION ALL
-- SELECT 
--     'market_price_daily' AS table_name, COUNT(*) AS record_count FROM market_price_daily
-- UNION ALL
-- SELECT 
--     'risk_free_rate_daily' AS table_name, COUNT(*) AS record_count FROM risk_free_rate_daily;
