# Housing Price Predictor — Multi-Stage Docker Build

A small end-to-end MLOps exercise: train a regression model on the California Housing dataset, package it with a multi-stage Docker build, and serve predictions through a Flask API — with the trained model persisted via a Docker volume.

This project was built as a hands-on learning exercise to understand **why** multi-stage builds, Docker volumes, and the separation of training/serving concerns matter in a real ML deployment pipeline — not just how to write the syntax.

## What this does

1. **Trains** a `RandomForestRegressor` on the California Housing dataset (median house price prediction from features like income, location, and room counts).
2. **Saves** the trained model and its `StandardScaler` as `.pkl` files.
3. **Serves** predictions through a lightweight Flask API, loading the saved model at runtime.
4. **Persists** the trained model in a Docker volume, so it survives container restarts without retraining.

## Why a multi-stage build?

Training and serving have very different dependency footprints:

|         | Training                           | Serving                                    |
| ------- | ---------------------------------- | ------------------------------------------ |
| Needs   | `pandas`, `scikit-learn`, `joblib` | `scikit-learn`, `joblib`, `flask`, `numpy` |
| Purpose | Runs once, produces an artifact    | Runs continuously, answers requests        |

Without multi-stage builds, the final image would carry `pandas` and the entire training toolchain into production — dead weight that's never used at runtime. With multi-stage builds, the `train` stage is used only to produce the `.pkl` files; only those files cross over into the final `serve` image via `COPY --from=train`. Everything else from the training stage — the intermediate layers, the unused dependencies — is discarded entirely.

## Why a Docker volume?

The model is copied into the image at build time, so scaling to multiple containers doesn't require retraining — each container already has its own copy baked in. The volume solves a different problem: if the model is **retrained later** (new data, a better model), the new `.pkl` needs somewhere to live that isn't tied to any single container's lifecycle. Mounting `/data` as a volume means an updated model can be written there — by a retraining job, for example — and picked up without rebuilding or redeploying the image.

_Note: at Kubernetes scale, across multiple nodes, this requires a `ReadWriteMany` storage backend (e.g. NFS, EFS) rather than a single-node volume — a distinction worth knowing even though this local exercise doesn't exercise it._

## Project structure

```
housing-app/
├── train/
│   ├── train.py              # Stage 1: trains the model, saves .pkl files
│   └── requirements-train.txt
├── serve/
│   ├── serve.py              # Stage 2: Flask API, loads .pkl files, serves predictions
│   └── requirements-serve.txt
└── Dockerfile
```

## Running it

**Build:**

```bash
docker build -t housing-app .
```

**Run (with a persistent volume for the model):**

```bash
docker run -d -p 5000:5000 -v modelo-vol:/data --name housing-container housing-app
```

**Health check:**

```bash
curl http://localhost:5000/health
```

**Get a prediction:**

```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"MedInc": 8.3252, "HouseAge": 41.0, "AveRooms": 6.984127, "AveBedrms": 1.023810, "Population": 322.0, "AveOccup": 2.555556, "Latitude": 37.88, "Longitude": -122.23}'
```

**Verify persistence** (the model survives a container's death):

```bash
docker rm -f housing-container
docker run -d -p 5000:5000 -v modelo-vol:/data --name housing-container housing-app
curl http://localhost:5000/health
```

## API

### `GET /health`

Returns `{"status": "ok"}` if the service is up.

### `POST /predict`

Request body (all fields required):

```json
{
    "MedInc": 8.3252,
    "HouseAge": 41.0,
    "AveRooms": 6.984127,
    "AveBedrms": 1.02381,
    "Population": 322.0,
    "AveOccup": 2.555556,
    "Latitude": 37.88,
    "Longitude": -122.23
}
```

Response:

```json
{
    "predicted_price_hundreds_of_thousands": 4.526
}
```

_Prices are in hundreds of thousands of USD, per the original dataset's units._

## Design decisions worth calling out

- **`RUN` vs `CMD`**: `train.py` runs via `RUN` during the build — it's a script that terminates and its only job is to produce an artifact. `serve.py` runs via `CMD` — it's a long-running process (the Flask server), so it belongs to container runtime, not build time. Putting a long-running server in `RUN` would hang the build indefinitely.
- **Separate `requirements` files**: dependencies are copied and installed _before_ the application code in the Dockerfile, so Docker's build cache can reuse the `pip install` layer when only the code changes — not the dependencies.
- **Scaler is saved alongside the model**: new inputs at prediction time need the _same_ scaling transformation the training data went through, so the fitted `StandardScaler` is persisted too, not just the model.

## What's next

- Explore `train` and `serve` as separate containers within the same Kubernetes Pod, rather than a single container with mixed concerns.
- Add liveness/readiness probes using the existing `/health` endpoint.
- Deploy with a `PersistentVolumeClaim` backed by a `ReadWriteMany` `StorageClass` to support multi-node scheduling.

---

Built as part of a structured self-study path into Docker, Kubernetes, and MLOps fundamentals.
