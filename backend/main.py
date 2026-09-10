from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ml.regime_classifier import RegimeClassifier
from ml.bias_corrector import BiasCorrector
from ml.probability_estimator import ProbabilityEstimator
from ml.synthetic_data import generate_training_data, generate_synthetic_forecast, compute_verification_metrics
import numpy as np

app = FastAPI(title="Regime-Aware Rainfall Post-Processing API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

regime_clf = RegimeClassifier()
bias_corr = BiasCorrector()
prob_est = ProbabilityEstimator()
_models_trained = False


def _ensure_models_trained():
    global _models_trained
    if not _models_trained:
        if not regime_clf.is_trained:
            regime_clf.load()
        if not bias_corr.is_trained:
            bias_corr.load()
        if not prob_est.is_trained:
            prob_est.load()
        if not regime_clf.is_trained:
            print("Training ML models on synthetic data...")
            df = generate_training_data(n_samples=6000, seed=42)
            regime_clf.train(df)
            regime_clf.save()
            bias_corr.train(df)
            bias_corr.save()
            prob_est.train(df)
            prob_est.save()
            print("ML models trained and saved.")
        _models_trained = True


@app.on_event("startup")
async def startup_event():
    _ensure_models_trained()


@app.get("/")
def root():
    return {"message": "Regime-Aware Rainfall Post-Processing API", "version": "1.0.0"}


@app.get("/api/v1/health")
def health():
    return {"status": "healthy", "models_loaded": _models_trained}


@app.get("/api/v1/forecast/process")
def process_forecast(date: str = "2026-09-09", lead_time: int = 24, model_source: str = "GFS"):
    forecast = generate_synthetic_forecast(forecast_date=date, lead_time=lead_time)
    regime = forecast["regime"]
    corrected_districts = []
    for d in forecast["districts"]:
        corrected = bias_corr.predict(
            raw_rainfall=d["raw"],
            features=regime["features"],
            regime=regime["type"],
            lead_time=lead_time,
        )
        probs = prob_est.predict(corrected, regime["features"], lead_time=lead_time)
        d["corrected"] = corrected
        d.update(probs)
        corrected_districts.append(d)
    return {
        "date": date,
        "lead_time": lead_time,
        "model_source": model_source,
        "regime": regime,
        "districts": corrected_districts,
    }


@app.get("/api/v1/regime/classify/{date}")
def classify_regime(date: str, lead_time: int = 24):
    forecast = generate_synthetic_forecast(forecast_date=date, lead_time=lead_time)
    return {
        "date": date,
        "regime": forecast["regime"],
    }


@app.get("/api/v1/forecast/district/{district_id}")
def get_district_forecast(district_id: int, date: str = "2026-09-09", lead_time: int = 24):
    forecast = generate_synthetic_forecast(forecast_date=date, lead_time=lead_time)
    regime = forecast["regime"]
    for d in forecast["districts"]:
        if d["district_id"] == district_id:
            corrected = bias_corr.predict(d["raw"], regime["features"], regime["type"], lead_time)
            probs = prob_est.predict(corrected, regime["features"], lead_time)
            d["corrected"] = corrected
            d.update(probs)
            return d
    return {"error": "District not found"}


@app.get("/api/v1/probability/map/{date}")
def get_probability_map(date: str, lead_time: int = 24):
    forecast = generate_synthetic_forecast(forecast_date=date, lead_time=lead_time)
    regime = forecast["regime"]
    districts = []
    for d in forecast["districts"]:
        corrected = bias_corr.predict(d["raw"], regime["features"], regime["type"], lead_time)
        probs = prob_est.predict(corrected, regime["features"], lead_time)
        districts.append({
            "district_id": d["district_id"],
            "name": d["name"],
            "state": d["state"],
            "lat": d["lat"],
            "lon": d["lon"],
            "corrected": corrected,
            **probs,
        })
    return {"date": date, "regime": regime["type"], "districts": districts}


@app.get("/api/v1/verification/report/{date}")
def get_verification_report(date: str, lead_time: int = 24):
    rng = np.random.RandomState(hash(date) % 2**31)
    n = 200
    observed = rng.exponential(30, n)
    raw_forecast = observed * rng.uniform(0.8, 1.5, n) + rng.normal(0, 8, n)
    corrected_forecast = observed * rng.uniform(0.9, 1.15, n) + rng.normal(0, 4, n)
    raw_metrics = compute_verification_metrics(observed, raw_forecast, threshold=64.5)
    corrected_metrics = compute_verification_metrics(observed, corrected_forecast, threshold=64.5)
    by_regime = {}
    for regime in ["active_monsoon", "break_monsoon", "depression", "orographic", "coastal", "western_disturbance"]:
        obs_r = rng.exponential(30, 50)
        raw_r = obs_r * rng.uniform(0.8, 1.5, 50) + rng.normal(0, 8, 50)
        corr_r = obs_r * rng.uniform(0.9, 1.15, 50) + rng.normal(0, 4, 50)
        by_regime[regime] = {
            "raw": compute_verification_metrics(obs_r, raw_r, 64.5),
            "corrected": compute_verification_metrics(obs_r, corr_r, 64.5),
        }
    by_lead_time = []
    for lt in [24, 48, 72, 96, 120]:
        obs_lt = rng.exponential(30, 100)
        noise_scale = 4 + (lt - 24) / 20.0
        raw_lt = obs_lt * rng.uniform(0.8, 1.5, 100) + rng.normal(0, noise_scale, 100)
        corr_lt = obs_lt * rng.uniform(0.9, 1.15, 100) + rng.normal(0, noise_scale * 0.6, 100)
        raw_m = compute_verification_metrics(obs_lt, raw_lt, 64.5)
        corr_m = compute_verification_metrics(obs_lt, corr_lt, 64.5)
        by_lead_time.append({
            "lead": f"T+{lt}",
            "raw_rmse": raw_m["rmse"],
            "corrected_rmse": corr_m["rmse"],
            "raw_ets": raw_m["ets"],
            "corrected_ets": corr_m["ets"],
        })
    return {
        "date": date,
        "lead_time": lead_time,
        "overall": {"raw": raw_metrics, "corrected": corrected_metrics},
        "by_regime": by_regime,
        "by_lead_time": by_lead_time,
    }


@app.get("/api/v1/forecast/table/{date}")
def get_forecast_table(date: str, lead_time: int = 24):
    forecast = generate_synthetic_forecast(forecast_date=date, lead_time=lead_time)
    regime = forecast["regime"]
    for d in forecast["districts"]:
        corrected = bias_corr.predict(d["raw"], regime["features"], regime["type"], lead_time)
        probs = prob_est.predict(corrected, regime["features"], lead_time)
        d["corrected"] = corrected
        d.update(probs)
    return {"date": date, "lead_time": lead_time, "districts": forecast["districts"]}
