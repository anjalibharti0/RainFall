from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./rainfall.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class District(Base):
    __tablename__ = "districts"
    district_id = Column(Integer, primary_key=True, index=True)
    district_name = Column(String(100))
    state_name = Column(String(100))
    centroid_lat = Column(Float)
    centroid_lon = Column(Float)
    zone = Column(String(50))


class RegimeClassification(Base):
    __tablename__ = "regime_classifications"
    id = Column(Integer, primary_key=True, index=True)
    forecast_date = Column(String(20))
    regime_label = Column(String(50))
    confidence = Column(Float)
    model_version = Column(String(20))
    features = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class CorrectedForecast(Base):
    __tablename__ = "corrected_forecasts"
    id = Column(Integer, primary_key=True, index=True)
    forecast_date = Column(String(20))
    lead_time = Column(Integer)
    district_id = Column(Integer)
    raw_rainfall = Column(Float)
    corrected_rainfall = Column(Float)
    regime_used = Column(String(50))
    model_version = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)


class RainfallProbability(Base):
    __tablename__ = "rainfall_probabilities"
    id = Column(Integer, primary_key=True, index=True)
    forecast_date = Column(String(20))
    lead_time = Column(Integer)
    district_id = Column(Integer)
    p_moderate = Column(Float)
    p_heavy = Column(Float)
    p_very_heavy = Column(Float)
    p_extreme = Column(Float)
    regime_used = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


class VerificationMetric(Base):
    __tablename__ = "verification_metrics"
    id = Column(Integer, primary_key=True, index=True)
    forecast_date = Column(String(20))
    lead_time = Column(Integer)
    region = Column(String(100))
    regime = Column(String(50))
    rmse = Column(Float)
    mae = Column(Float)
    bias_ratio = Column(Float)
    ets = Column(Float)
    csi = Column(Float)
    pod = Column(Float)
    far = Column(Float)
    fss = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
